.PHONY: smoke live-smoke web test clean

smoke:
	python3 scripts/run.py --input data/sample_inventory.csv --output output/sample_recall_report.md --csv-output output/sample_recall_matches.csv --source sample

live-smoke:
	python3 scripts/run.py --input data/sample_inventory.csv --output output/live_recall_report.md --csv-output output/live_recall_matches.csv --source live --max-alerts 12 --extra-alert-url https://www.gov.uk/product-safety-alerts-reports-recalls/product-recall-azara-travel-adaptor-2601-0270 --extra-alert-url https://www.gov.uk/drug-device-alerts/class-2-medicines-recall-becton-dickinson-uk-ltd-chloraprep-2-percent-1ml-and-chloraprep-frepp-2-percent-1-dot-5ml-applicators-el-26-a-slash-26 --use-llm --env-file "$${OPENROUTER_ENV_FILE:-}" --model "$${OPENROUTER_MODEL:-qwen/qwen3.7-plus}"

web:
	python3 ../../scripts/local_web_shell.py --app-root .

test:
	python3 -m pytest -q

clean:
	rm -f output/sample_recall_report.md output/sample_recall_matches.csv output/live_recall_report.md output/live_recall_matches.csv output/alert_cache.json data/web_inventory.csv
