from pathlib import Path
import os
import subprocess
import sys


def run_cli(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    root = Path(__file__).resolve().parents[1]
    return subprocess.run(
        [sys.executable, "scripts/run.py", *args],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )


def test_sample_cli_generates_recall_outputs():
    root = Path(__file__).resolve().parents[1]
    report = root / "output" / "sample_recall_report.md"
    matches = root / "output" / "sample_recall_matches.csv"
    report.unlink(missing_ok=True)
    matches.unlink(missing_ok=True)

    result = run_cli(
        "--input",
        "data/sample_inventory.csv",
        "--output",
        "output/sample_recall_report.md",
        "--csv-output",
        "output/sample_recall_matches.csv",
        "--source",
        "sample",
    )

    assert result.returncode == 0, result.stderr
    assert report.exists()
    report_text = report.read_text()
    assert "# Recall Radar Report" in report_text
    assert "ADP-001" in report_text
    assert "exact_barcode" in report_text
    assert "Candidate manual comparisons avoided" in report_text

    assert matches.exists()
    csv_text = matches.read_text()
    assert "ADP-001" in csv_text
    assert "MED-001" in csv_text
    assert "SAFE-001" not in csv_text


def test_missing_input_exits_nonzero():
    result = run_cli("--input", "data/missing.csv")

    assert result.returncode != 0
    assert "Input file not found" in (result.stdout + result.stderr)


def test_use_llm_without_key_exits_nonzero():
    env = os.environ.copy()
    env.pop("OPENROUTER_API_KEY", None)

    result = run_cli("--source", "sample", "--use-llm", env=env)

    assert result.returncode != 0
    assert "Missing OPENROUTER_API_KEY for --use-llm" in (result.stdout + result.stderr)
