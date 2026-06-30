.PHONY: smoke web test clean

smoke:
	python3 scripts/run.py --input data/sample_input.txt --output output/sample_output.md

web:
	python3 ../../scripts/local_web_shell.py --app-root .

test:
	python3 -m pytest -q

clean:
	rm -f output/sample_output.md data/web_input.txt
