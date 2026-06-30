#!/usr/bin/env python3
"""Recall Radar: match local inventory rows against public safety recalls."""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TypedDict
from urllib.parse import urlparse

import feedparser
import httpx
from bs4 import BeautifulSoup
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field
from rapidfuzz import fuzz


INVENTORY_HEADERS = [
    "sku",
    "name",
    "brand",
    "model",
    "barcode",
    "gtin",
    "batch",
    "expiry_date",
    "location",
    "quantity",
]
OUTPUT_HEADERS = [
    "sku",
    "location",
    "quantity",
    "item_name",
    "alert_title",
    "source",
    "risk_level",
    "match_type",
    "confidence",
    "matched_fields",
    "action",
    "human_next_step",
    "alert_url",
]
FEED_URLS = [
    "https://www.gov.uk/product-safety-alerts-reports-recalls.atom",
    "https://www.gov.uk/drug-device-alerts.atom",
]
USER_AGENT = "RecallRadar/0.1 local daily automation"
DEFAULT_MODEL = "qwen/qwen3.7-plus"
ALLOWED_ENV_KEYS = {"OPENROUTER_API_KEY", "OPENROUTER_MODEL", "OPENROUTER_BASE_URL"}
KEYLIKE_RE = re.compile(r"(?i)(api[_-]?key|authorization|bearer|sk-[a-z0-9]|openrouter[_-]?api[_-]?key)")
IDENTIFIER_RE = re.compile(r"\b[A-Z0-9][A-Z0-9._/-]{3,}[A-Z0-9]\b", re.IGNORECASE)
GTIN_RE = re.compile(r"\b\d{8,14}\b")


class InventoryItem(BaseModel):
    sku: str
    name: str
    brand: str
    model: str | None
    barcode: str | None
    gtin: str | None
    batch: str | None
    expiry_date: str | None
    location: str
    quantity: int


class AlertRecord(BaseModel):
    source: str
    title: str
    url: str
    published: str | None
    alert_type: str | None
    risk_level: str | None
    product_name: str | None
    brand: str | None
    model: str | None
    barcode: str | None
    gtins: list[str] = Field(default_factory=list)
    batches: list[str] = Field(default_factory=list)
    hazard: str | None
    corrective_action: str | None
    advice: str | None
    raw_confidence: str


class MatchResult(BaseModel):
    sku: str
    location: str
    quantity: int
    alert_title: str
    alert_url: str
    source: str
    risk_level: str | None
    match_type: str
    confidence: int
    matched_fields: list[str]
    action: str
    human_next_step: str


class RecallState(TypedDict):
    inventory_items: list[InventoryItem]
    raw_alerts: list[dict[str, Any]]
    alerts: list[AlertRecord]
    matches: list[MatchResult]
    metrics: dict[str, Any]
    errors: list[str]
    output_path: str
    csv_output_path: str


def clean_cell(value: Any) -> str:
    return "" if value is None else str(value).strip()


def optional_cell(value: Any) -> str | None:
    cleaned = clean_cell(value)
    return cleaned or None


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value.casefold()).strip()


def normalize_identifier(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"[^A-Za-z0-9]", "", value).upper()


def compact_text(value: str | None, limit: int = 12000) -> str:
    if not value:
        return ""
    return re.sub(r"\n{3,}", "\n\n", re.sub(r"[ \t]+", " ", value)).strip()[:limit]


def parse_quantity(value: Any) -> int:
    cleaned = clean_cell(value)
    if not cleaned:
        return 0
    return int(cleaned)


def parse_inventory(path: Path) -> list[InventoryItem]:
    if not path.exists():
        raise SystemExit(f"Input file not found: {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != INVENTORY_HEADERS:
            raise SystemExit("Input CSV headers must be exactly: " + ",".join(INVENTORY_HEADERS))
        items: list[InventoryItem] = []
        for row in reader:
            items.append(
                InventoryItem(
                    sku=clean_cell(row.get("sku")),
                    name=clean_cell(row.get("name")),
                    brand=clean_cell(row.get("brand")),
                    model=optional_cell(row.get("model")),
                    barcode=optional_cell(row.get("barcode")),
                    gtin=optional_cell(row.get("gtin")),
                    batch=optional_cell(row.get("batch")),
                    expiry_date=optional_cell(row.get("expiry_date")),
                    location=clean_cell(row.get("location")),
                    quantity=parse_quantity(row.get("quantity")),
                )
            )
    return items


def load_private_env(path_value: str | None) -> None:
    if not path_value or not path_value.strip():
        return
    path = Path(path_value).expanduser()
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key not in ALLOWED_ENV_KEYS:
            continue
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def read_sample_alerts(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise SystemExit(f"Sample alerts file not found: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return [dict(item) for item in payload]
    if isinstance(payload, dict):
        alerts = payload.get("alerts", payload.get("records", []))
        if isinstance(alerts, list):
            return [dict(item) for item in alerts]
    raise SystemExit("Sample alerts JSON must be a list or contain an alerts list")


def parse_feed_links(xml_text: str) -> list[dict[str, str | None]]:
    parsed = feedparser.parse(xml_text)
    links: list[dict[str, str | None]] = []
    for entry in parsed.entries:
        link = clean_cell(getattr(entry, "link", ""))
        if not link:
            continue
        links.append(
            {
                "url": link,
                "title": clean_cell(getattr(entry, "title", "")) or None,
                "published": clean_cell(getattr(entry, "published", ""))
                or clean_cell(getattr(entry, "updated", ""))
                or None,
            }
        )
    return links


def fetch_live_alerts(max_alerts: int, extra_urls: list[str], cache_path: Path) -> list[dict[str, Any]]:
    headers = {"User-Agent": USER_AGENT}
    page_targets: list[dict[str, str | None]] = []
    with httpx.Client(timeout=20, headers=headers, follow_redirects=True) as client:
        for feed_url in FEED_URLS:
            if len(page_targets) >= max_alerts:
                break
            response = client.get(feed_url)
            response.raise_for_status()
            remaining = max(0, max_alerts - len(page_targets))
            page_targets.extend(parse_feed_links(response.text)[:remaining])

        for extra_url in extra_urls:
            if extra_url:
                page_targets.append({"url": extra_url, "title": None, "published": None})

        raw_alerts: list[dict[str, Any]] = []
        cache_records: list[dict[str, str | None]] = []
        seen_urls: set[str] = set()
        for target in page_targets:
            url = clean_cell(target.get("url"))
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            response = client.get(url)
            response.raise_for_status()
            html = response.text
            soup = BeautifulSoup(html, "html.parser")
            title = target.get("title") or extract_html_title(soup) or url
            published = target.get("published") or extract_published(soup)
            text = extract_visible_text(soup)
            raw_alert = {
                "url": url,
                "title": title,
                "published": published,
                "html": html,
                "text": text,
            }
            raw_alerts.append(raw_alert)
            cache_records.append(
                {
                    "url": url,
                    "title": title,
                    "published": published,
                    "text": compact_text(text, limit=20000),
                }
            )

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(cache_records, indent=2, ensure_ascii=False), encoding="utf-8")
    return raw_alerts


def extract_html_title(soup: BeautifulSoup) -> str | None:
    h1 = soup.find("h1")
    if h1:
        title = h1.get_text(" ", strip=True)
        if title:
            return title
    if soup.title and soup.title.string:
        return soup.title.string.strip()
    return None


def extract_published(soup: BeautifulSoup) -> str | None:
    for selector in ["time[datetime]", "meta[property='article:published_time']", "meta[name='govuk:public-updated-at']"]:
        node = soup.select_one(selector)
        if not node:
            continue
        value = node.get("datetime") or node.get("content") or node.get_text(" ", strip=True)
        if value:
            return value.strip()
    text = extract_visible_text(soup)
    match = re.search(r"(?i)published\s+([0-9]{1,2}\s+[A-Z][a-z]+\s+[0-9]{4})", text)
    return match.group(1) if match else None


def extract_visible_text(soup: BeautifulSoup) -> str:
    for node in soup(["script", "style", "noscript", "svg"]):
        node.decompose()
    main = soup.find("main") or soup.body or soup
    return compact_text(main.get_text("\n", strip=True), limit=50000)


def source_from_url(url: str) -> str:
    path = urlparse(url).path.casefold()
    if "drug-device-alert" in path or "medicines-recall" in path:
        return "MHRA/GOV.UK drug and device alerts"
    if "product-safety" in path or "product-recall" in path:
        return "OPSS/GOV.UK product safety alerts"
    return "GOV.UK recall alert"


def collect_label_values(soup: BeautifulSoup) -> dict[str, list[str]]:
    pairs: dict[str, list[str]] = {}

    def add(label: str, value: str) -> None:
        key = normalize_text(label).rstrip(":")
        cleaned = compact_text(value, limit=1000)
        if key and cleaned:
            pairs.setdefault(key, []).append(cleaned)

    for row in soup.select(".govuk-summary-list__row"):
        key_node = row.select_one(".govuk-summary-list__key")
        value_node = row.select_one(".govuk-summary-list__value")
        if key_node and value_node:
            add(key_node.get_text(" ", strip=True), value_node.get_text(" ", strip=True))

    for dt in soup.find_all("dt"):
        dd = dt.find_next_sibling("dd")
        if dd:
            add(dt.get_text(" ", strip=True), dd.get_text(" ", strip=True))

    for row in soup.find_all("tr"):
        cells = row.find_all(["th", "td"])
        if len(cells) >= 2:
            add(cells[0].get_text(" ", strip=True), cells[1].get_text(" ", strip=True))

    for paragraph in soup.find_all(["p", "li"]):
        text = paragraph.get_text(" ", strip=True)
        if ":" in text and len(text) <= 300:
            label, value = text.split(":", 1)
            if 2 <= len(label) <= 60:
                add(label, value)
    return pairs


def find_first_label(pairs: dict[str, list[str]], keywords: list[str]) -> str | None:
    for key, values in pairs.items():
        if any(keyword in key for keyword in keywords):
            for value in values:
                if value:
                    return value
    return None


def find_many_label(pairs: dict[str, list[str]], keywords: list[str]) -> list[str]:
    values: list[str] = []
    for key, found in pairs.items():
        if any(keyword in key for keyword in keywords):
            values.extend(found)
    return split_identifier_values(values)


def split_identifier_values(values: list[str]) -> list[str]:
    seen: set[str] = set()
    identifiers: list[str] = []
    for value in values:
        for part in re.split(r"[,;\n]|\s+and\s+", value):
            cleaned = part.strip().strip(".:")
            if not cleaned:
                continue
            normalized = normalize_identifier(cleaned)
            if normalized and normalized not in seen:
                seen.add(normalized)
                identifiers.append(cleaned)
    return identifiers


def extract_risk_level(text: str, pairs: dict[str, list[str]]) -> str | None:
    labelled = find_first_label(pairs, ["risk", "alert level", "class"])
    if labelled:
        return labelled
    for pattern in [r"(?i)class\s+[123]\b", r"(?i)(serious|high|medium|low)\s+risk"]:
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    return None


def extract_section_text(soup: BeautifulSoup, headings: list[str]) -> str | None:
    for heading in soup.find_all(re.compile("^h[2-4]$")):
        heading_text = normalize_text(heading.get_text(" ", strip=True))
        if not any(wanted in heading_text for wanted in headings):
            continue
        chunks: list[str] = []
        for sibling in heading.find_next_siblings():
            if sibling.name and re.fullmatch(r"h[1-4]", sibling.name):
                break
            if sibling.name in {"p", "ul", "ol", "table", "div"}:
                text = sibling.get_text(" ", strip=True)
                if text:
                    chunks.append(text)
            if len(" ".join(chunks)) > 1200:
                break
        if chunks:
            return compact_text(" ".join(chunks), limit=1500)
    return None


def extract_identifiers_from_text(text: str, hint_words: list[str]) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in lines:
        lowered = normalize_text(line)
        if not any(hint in lowered for hint in hint_words):
            continue
        for identifier in IDENTIFIER_RE.findall(line):
            normalized = normalize_identifier(identifier)
            if normalized and normalized not in seen and not normalized.isdigit():
                seen.add(normalized)
                found.append(identifier.strip())
        for identifier in GTIN_RE.findall(line):
            if identifier not in seen:
                seen.add(identifier)
                found.append(identifier)
    return found


def deterministic_alert_from_html(raw: dict[str, Any]) -> AlertRecord:
    html = clean_cell(raw.get("html"))
    soup = BeautifulSoup(html, "html.parser") if html else BeautifulSoup("", "html.parser")
    text = clean_cell(raw.get("text")) or extract_visible_text(soup)
    pairs = collect_label_values(soup)
    title = clean_cell(raw.get("title")) or extract_html_title(soup) or clean_cell(raw.get("url"))
    url = clean_cell(raw.get("url"))
    barcode = find_first_label(pairs, ["barcode", "bar code"])
    labelled_gtins = find_many_label(pairs, ["gtin", "ean"])
    text_gtins = [value for value in GTIN_RE.findall(text) if len(value) >= 8]
    if barcode and GTIN_RE.fullmatch(barcode.strip()):
        text_gtins.append(barcode)
    gtins = unique_values(labelled_gtins + text_gtins)
    model = find_first_label(pairs, ["model", "model number", "product code"])
    if not model:
        model_candidates = extract_identifiers_from_text(text, ["model", "product code"])
        model = model_candidates[0] if model_candidates else None
    batches = unique_values(find_many_label(pairs, ["batch", "lot", "serial"]) + extract_identifiers_from_text(text, ["batch", "lot"]))
    product_name = find_first_label(pairs, ["product", "medicine", "device"])
    brand = find_first_label(pairs, ["brand", "manufacturer", "company", "product owner"])
    hazard = extract_section_text(soup, ["hazard", "risk", "problem", "issue", "defect"])
    advice = extract_section_text(soup, ["advice", "what you need to do", "action for", "customer action"])
    corrective_action = extract_section_text(soup, ["corrective", "recall", "action", "remedy"])
    alert_type = find_first_label(pairs, ["alert type", "product alert", "notice type", "category"])
    risk_level = extract_risk_level(text, pairs)
    return AlertRecord(
        source=source_from_url(url),
        title=title,
        url=url,
        published=optional_cell(raw.get("published")) or extract_published(soup),
        alert_type=alert_type,
        risk_level=risk_level,
        product_name=product_name or title,
        brand=brand,
        model=model,
        barcode=barcode,
        gtins=gtins,
        batches=batches,
        hazard=hazard,
        corrective_action=corrective_action,
        advice=advice,
        raw_confidence="deterministic_html",
    )


def unique_values(values: list[str | None]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        cleaned = optional_cell(value)
        if not cleaned:
            continue
        normalized = normalize_identifier(cleaned) or normalize_text(cleaned)
        if normalized in seen:
            continue
        seen.add(normalized)
        result.append(cleaned)
    return result


def normalized_sample_alert(raw: dict[str, Any]) -> AlertRecord:
    payload = dict(raw)
    payload.setdefault("source", "sample")
    payload.setdefault("title", payload.get("product_name") or "Sample recall alert")
    payload.setdefault("url", "sample://recall-alert")
    payload.setdefault("published", None)
    payload.setdefault("alert_type", None)
    payload.setdefault("risk_level", None)
    payload.setdefault("product_name", None)
    payload.setdefault("brand", None)
    payload.setdefault("model", None)
    payload.setdefault("barcode", None)
    payload.setdefault("gtins", [])
    payload.setdefault("batches", [])
    payload.setdefault("hazard", None)
    payload.setdefault("corrective_action", None)
    payload.setdefault("advice", None)
    payload.setdefault("raw_confidence", "sample_fixture")
    if isinstance(payload.get("gtins"), str):
        payload["gtins"] = split_identifier_values([payload["gtins"]])
    if isinstance(payload.get("batches"), str):
        payload["batches"] = split_identifier_values([payload["batches"]])
    return AlertRecord(**payload)


def needs_llm_fill(alert: AlertRecord) -> bool:
    return any(
        value in (None, [], "")
        for value in [alert.product_name, alert.brand, alert.model, alert.barcode, alert.gtins, alert.batches, alert.hazard, alert.corrective_action, alert.advice]
    )

def relevant_to_inventory(alert: AlertRecord, raw: dict[str, Any], items: list[InventoryItem]) -> bool:
    haystack_text = normalize_text(
        " ".join(
            clean_cell(value)
            for value in [
                alert.title,
                alert.product_name,
                alert.brand,
                alert.model,
                raw.get("title"),
                raw.get("text"),
            ]
        )
    )
    haystack_ids = normalize_identifier(
        " ".join(
            clean_cell(value)
            for value in [
                alert.title,
                alert.product_name,
                alert.brand,
                alert.model,
                alert.barcode,
                " ".join(alert.gtins),
                raw.get("title"),
                raw.get("text"),
            ]
        )
    )
    for item in items:
        for identifier in [item.barcode, item.gtin, item.model]:
            normalized = normalize_identifier(identifier)
            if normalized and normalized in haystack_ids:
                return True
        brand = normalize_text(item.brand)
        name = normalize_text(item.name)
        if brand and brand in haystack_text:
            return True
        name_tokens = [token for token in re.split(r"[^a-z0-9]+", name) if len(token) >= 5]
        if name_tokens and sum(1 for token in name_tokens if token in haystack_text) >= min(2, len(name_tokens)):
            return True
    return False


def force_no_extra_properties(schema: dict[str, Any]) -> dict[str, Any]:
    if schema.get("type") == "object":
        schema["additionalProperties"] = False
        for subschema in schema.get("properties", {}).values():
            if isinstance(subschema, dict):
                force_no_extra_properties(subschema)
    for key in ("$defs", "definitions"):
        for subschema in schema.get(key, {}).values():
            if isinstance(subschema, dict):
                force_no_extra_properties(subschema)
    if isinstance(schema.get("items"), dict):
        force_no_extra_properties(schema["items"])
    for key in ("anyOf", "oneOf", "allOf"):
        for subschema in schema.get(key, []):
            if isinstance(subschema, dict):
                force_no_extra_properties(subschema)
    return schema


def llm_fill_alert(alert: AlertRecord, raw: dict[str, Any], model: str) -> AlertRecord:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise SystemExit("Missing OPENROUTER_API_KEY for --use-llm")
    base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").rstrip("/")
    schema = force_no_extra_properties(AlertRecord.model_json_schema())
    body = {
        "model": model,
        "temperature": 0,
        "max_tokens": 1200,
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": "recall_alert", "strict": True, "schema": schema},
        },
        "messages": [
            {
                "role": "system",
                "content": (
                    "Extract a recall alert into the requested JSON schema. Fill missing fields from public page text. "
                    "Do not invent identifiers; use null or empty lists when absent."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "source": alert.source,
                        "url": alert.url,
                        "title": alert.title,
                        "published": alert.published,
                        "deterministic_fields": alert.model_dump(),
                        "page_text": compact_text(clean_cell(raw.get("text")), limit=9000),
                    },
                    ensure_ascii=False,
                ),
            },
        ],
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-OpenRouter-Title": "Recall Radar",
        "HTTP-Referer": "https://github.com/AnasInno/daily-ai-automation-kit",
    }
    response = httpx.post(f"{base_url}/chat/completions", headers=headers, json=body, timeout=20)
    if response.status_code < 200 or response.status_code >= 300:
        if KEYLIKE_RE.search(response.text or ""):
            raise SystemExit(f"OpenRouter request failed: {response.status_code}")
        raise SystemExit(f"OpenRouter request failed: {response.status_code}")
    try:
        content = response.json()["choices"][0]["message"]["content"]
        parsed_content = json.loads(content)
        if not isinstance(parsed_content, dict):
            raise ValueError("OpenRouter content was not a JSON object")
        llm_payload = alert.model_dump()
        llm_payload.update(parsed_content)
        if not llm_payload.get("raw_confidence"):
            llm_payload["raw_confidence"] = "openrouter_fill"
        llm_alert = AlertRecord(**llm_payload)
    except Exception as exc:  # noqa: BLE001 - keep CLI failure concise for malformed model output.
        raise SystemExit(f"OpenRouter response could not be parsed: {exc}") from exc
    return merge_alert_fill(alert, llm_alert)


def merge_alert_fill(deterministic: AlertRecord, llm_alert: AlertRecord) -> AlertRecord:
    merged = deterministic.model_dump()
    llm_payload = llm_alert.model_dump()
    protected = {"source", "url", "title"}
    protected_identifiers = {"barcode", "gtins", "model"}
    for field, value in llm_payload.items():
        current = merged.get(field)
        if field in protected:
            continue
        if field in protected_identifiers and current not in (None, [], ""):
            continue
        if current in (None, [], "") and value not in (None, [], ""):
            merged[field] = value
    merged["raw_confidence"] = "deterministic_html+openrouter_fill"
    return AlertRecord(**merged)


def evaluate_match(item: InventoryItem, alert: AlertRecord) -> MatchResult | None:
    item_barcode = normalize_identifier(item.barcode)
    alert_barcode = normalize_identifier(alert.barcode)
    if item_barcode and alert_barcode and item_barcode == alert_barcode:
        return build_match(item, alert, "exact_barcode", 99, ["barcode"])

    item_gtin = normalize_identifier(item.gtin)
    alert_gtins = {normalize_identifier(value) for value in alert.gtins if normalize_identifier(value)}
    if item_gtin and item_gtin in alert_gtins:
        return build_match(item, alert, "exact_gtin", 99, ["gtin"])

    item_brand = normalize_text(item.brand)
    alert_brand = normalize_text(alert.brand)
    item_model = normalize_identifier(item.model)
    alert_model = normalize_identifier(alert.model)
    if item_brand and alert_brand and item_brand == alert_brand and item_model and item_model == alert_model:
        return build_match(item, alert, "brand_model", 92, ["brand", "model"])

    alert_product = alert.product_name or alert.title
    if item.brand and alert_product:
        brand_name_score = fuzz.token_set_ratio(f"{item.brand} {item.name}", f"{alert.brand or ''} {alert_product}")
        if brand_name_score >= 85:
            return build_match(item, alert, "fuzzy_brand_name", 80, ["brand", "name"])

    if alert_product:
        name_score = fuzz.token_set_ratio(item.name, alert_product)
        if name_score >= 90:
            return build_match(item, alert, "fuzzy_name_review", 70, ["name"])

    return None


def build_match(item: InventoryItem, alert: AlertRecord, match_type: str, confidence: int, fields: list[str]) -> MatchResult:
    if confidence >= 90:
        action = alert.corrective_action or "Quarantine matching stock and check the recall notice before use or sale."
        human_next_step = "Open the alert URL and verify identifiers, batch, and quantity before taking stock action."
    else:
        action = alert.advice or "Review this possible recall match before taking action."
        human_next_step = "Compare the product name, brand, model, barcode, GTIN, and batch against the alert page."
    return MatchResult(
        sku=item.sku,
        location=item.location,
        quantity=item.quantity,
        alert_title=alert.title,
        alert_url=alert.url,
        source=alert.source,
        risk_level=alert.risk_level,
        match_type=match_type,
        confidence=confidence,
        matched_fields=fields,
        action=action,
        human_next_step=human_next_step,
    )


def match_inventory_items(items: list[InventoryItem], alerts: list[AlertRecord]) -> list[MatchResult]:
    best: dict[tuple[str, str], MatchResult] = {}
    precedence = {
        "exact_barcode": 5,
        "exact_gtin": 4,
        "brand_model": 3,
        "fuzzy_brand_name": 2,
        "fuzzy_name_review": 1,
    }
    for item in items:
        for alert in alerts:
            match = evaluate_match(item, alert)
            if not match:
                continue
            key = (match.sku, match.alert_url)
            existing = best.get(key)
            if not existing:
                best[key] = match
                continue
            current_rank = (match.confidence, precedence.get(match.match_type, 0))
            existing_rank = (existing.confidence, precedence.get(existing.match_type, 0))
            if current_rank > existing_rank:
                best[key] = match
    return sorted(best.values(), key=lambda m: (-m.confidence, m.sku, m.alert_title))


def render_csv(path: Path, matches: list[MatchResult], inventory_by_sku: dict[str, InventoryItem]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_HEADERS)
        writer.writeheader()
        for match in matches:
            item = inventory_by_sku[match.sku]
            writer.writerow(
                {
                    "sku": match.sku,
                    "location": match.location,
                    "quantity": match.quantity,
                    "item_name": item.name,
                    "alert_title": match.alert_title,
                    "source": match.source,
                    "risk_level": match.risk_level or "",
                    "match_type": match.match_type,
                    "confidence": match.confidence,
                    "matched_fields": ";".join(match.matched_fields),
                    "action": match.action,
                    "human_next_step": match.human_next_step,
                    "alert_url": match.alert_url,
                }
            )


def render_markdown(state: RecallState, runtime_seconds: float) -> str:
    items = state["inventory_items"]
    alerts = state["alerts"]
    matches = state["matches"]
    matched_skus = {match.sku for match in matches}
    action_matches = [match for match in matches if match.confidence >= 90]
    review_matches = [match for match in matches if match.confidence < 90]
    comparisons = len(alerts) * len(items)
    source_names = sorted({alert.source for alert in alerts})
    lines = [
        "# Recall Radar Report",
        "",
        "## Summary",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        f"Inventory rows checked: {len(items)}",
        f"Alerts reviewed: {len(alerts)}",
        f"Matched inventory rows: {len(matched_skus)}",
        f"Rows needing human review: {len(matches)}",
        "",
    ]
    if not matches:
        lines.extend(["No likely inventory matches found", ""])

    lines.extend(["## Action required", ""])
    if action_matches:
        for match in action_matches:
            lines.extend(format_match_bullet(match, state))
    else:
        lines.extend(["No exact high-confidence recall matches found.", ""])

    lines.extend(["## Review queue", ""])
    if review_matches:
        for match in review_matches:
            lines.extend(format_match_bullet(match, state))
    else:
        lines.extend(["No fuzzy review matches found.", ""])

    lines.extend(
        [
            "## No-match inventory count",
            "",
            f"Inventory rows without a likely alert match: {len(items) - len(matched_skus)}",
            "",
            "## Time saved proxy",
            "",
            f"Alerts reviewed: {len(alerts)}",
            f"Inventory rows checked: {len(items)}",
            f"Candidate manual comparisons avoided = alerts * inventory rows: {comparisons}",
            f"Rows needing human review: {len(matches)}",
            f"Automation runtime seconds: {runtime_seconds:.2f}",
            "",
            "The operator now reviews only the matched/review rows instead of opening every alert against every stock row.",
            "",
            "## Source notes",
            "",
        ]
    )
    if source_names:
        for source in source_names:
            lines.append(f"- {source}")
    else:
        lines.append("- No alert sources were loaded.")
    lines.append(f"- OpenRouter extraction: {state['metrics'].get('openrouter_extraction', 'disabled')}")
    if state["metrics"].get("model"):
        lines.append(f"- OpenRouter model: {state['metrics']['model']}")
    if state["metrics"].get("openrouter_extraction") == "enabled":
        lines.append(f"- OpenRouter pages structured: {state['metrics'].get('openrouter_pages', 0)}")
    lines.extend(
        [
            "",
            f"Output CSV: {state['csv_output_path']}",
            "",
            "## Limitations",
            "",
            "Recall Radar is a stock-to-alert triage aid, not legal, clinical, or safety certification.",
            "Exact identifier matches are strongest; fuzzy name matches must be checked by a person before action.",
            "Public pages can change structure, so live extraction may miss fields that are visible to a human.",
            "",
        ]
    )
    return "\n".join(lines)


def format_match_bullet(match: MatchResult, state: RecallState) -> list[str]:
    inventory_by_sku = {item.sku: item for item in state["inventory_items"]}
    item = inventory_by_sku[match.sku]
    return [
        f"- `{match.sku}` — {item.name} at {match.location} (qty {match.quantity})",
        f"  - Alert: {match.alert_title}",
        f"  - Match: {match.match_type} ({match.confidence}) via {', '.join(match.matched_fields)}",
        f"  - Action: {match.action}",
        f"  - Human next step: {match.human_next_step}",
        f"  - Source: {match.alert_url}",
        "",
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Match local inventory against recall alerts.")
    parser.add_argument("--input", default="data/sample_inventory.csv")
    parser.add_argument("--output", default="output/sample_recall_report.md")
    parser.add_argument("--csv-output", default="output/sample_recall_matches.csv")
    parser.add_argument("--source", choices=["sample", "live"], default="sample")
    parser.add_argument("--sample-alerts", default="data/sample_alerts.json")
    parser.add_argument("--max-alerts", type=int, default=12)
    parser.add_argument("--extra-alert-url", action="append", default=[])
    parser.add_argument("--use-llm", action="store_true")
    parser.add_argument("--env-file", default="")
    parser.add_argument("--model", default=None)
    parser.add_argument("--cache", default="output/alert_cache.json")
    return parser


def build_graph(args: argparse.Namespace, started_at: float):
    def load_inventory(state: RecallState) -> dict[str, Any]:
        items = parse_inventory(Path(args.input))
        metrics = dict(state["metrics"])
        metrics["inventory_rows_checked"] = len(items)
        return {"inventory_items": items, "metrics": metrics}

    def load_alerts(state: RecallState) -> dict[str, Any]:
        if args.source == "sample":
            raw_alerts = read_sample_alerts(Path(args.sample_alerts))
        else:
            raw_alerts = fetch_live_alerts(args.max_alerts, args.extra_alert_url or [], Path(args.cache))
        metrics = dict(state["metrics"])
        metrics["raw_alerts_loaded"] = len(raw_alerts)
        return {"raw_alerts": raw_alerts, "metrics": metrics}

    def extract_alerts(state: RecallState) -> dict[str, Any]:
        alerts: list[AlertRecord] = []
        errors = list(state["errors"])
        llm_calls = 0
        for raw in state["raw_alerts"]:
            try:
                alert = normalized_sample_alert(raw) if args.source == "sample" else deterministic_alert_from_html(raw)
                if args.use_llm and needs_llm_fill(alert) and relevant_to_inventory(alert, raw, state["inventory_items"]):
                    alert = llm_fill_alert(alert, raw, args.model)
                    llm_calls += 1
                alerts.append(alert)
            except SystemExit:
                raise
            except Exception as exc:  # noqa: BLE001 - keep processing independent public pages.
                errors.append(f"Could not extract alert {raw.get('url', raw.get('title', 'unknown'))}: {exc}")
        metrics = dict(state["metrics"])
        metrics["alerts_reviewed"] = len(alerts)
        metrics["openrouter_extraction"] = "enabled" if args.use_llm else "disabled"
        metrics["model"] = args.model if args.use_llm else None
        metrics["openrouter_pages"] = llm_calls
        return {"alerts": alerts, "errors": errors, "metrics": metrics}

    def match_inventory(state: RecallState) -> dict[str, Any]:
        matches = match_inventory_items(state["inventory_items"], state["alerts"])
        metrics = dict(state["metrics"])
        metrics["rows_needing_human_review"] = len(matches)
        metrics["candidate_manual_comparisons_avoided"] = len(state["inventory_items"]) * len(state["alerts"])
        return {"matches": matches, "metrics": metrics}

    def render_outputs(state: RecallState) -> dict[str, Any]:
        runtime_seconds = time.time() - started_at
        output_path = Path(state["output_path"])
        csv_output_path = Path(state["csv_output_path"])
        inventory_by_sku = {item.sku: item for item in state["inventory_items"]}
        render_csv(csv_output_path, state["matches"], inventory_by_sku)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(render_markdown(state, runtime_seconds), encoding="utf-8")
        metrics = dict(state["metrics"])
        metrics["automation_runtime_seconds"] = runtime_seconds
        return {"metrics": metrics}

    graph = StateGraph(RecallState)
    graph.add_node("load_inventory", load_inventory)
    graph.add_node("load_alerts", load_alerts)
    graph.add_node("extract_alerts", extract_alerts)
    graph.add_node("match_inventory", match_inventory)
    graph.add_node("render_outputs", render_outputs)
    graph.add_edge(START, "load_inventory")
    graph.add_edge("load_inventory", "load_alerts")
    graph.add_edge("load_alerts", "extract_alerts")
    graph.add_edge("extract_alerts", "match_inventory")
    graph.add_edge("match_inventory", "render_outputs")
    graph.add_edge("render_outputs", END)
    return graph.compile()


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    load_private_env(args.env_file)
    args.model = args.model or os.getenv("OPENROUTER_MODEL", DEFAULT_MODEL)
    if args.use_llm and not os.getenv("OPENROUTER_API_KEY"):
        raise SystemExit("Missing OPENROUTER_API_KEY for --use-llm")

    started_at = time.time()
    graph = build_graph(args, started_at)
    initial_state: RecallState = {
        "inventory_items": [],
        "raw_alerts": [],
        "alerts": [],
        "matches": [],
        "metrics": {},
        "errors": [],
        "output_path": args.output,
        "csv_output_path": args.csv_output,
    }
    graph.invoke(initial_state)
    print(f"Wrote {Path(args.output)}")
    print(f"Wrote {Path(args.csv_output)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
