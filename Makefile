.PHONY: check

check:
	python3 scripts/check_public_repo.py
	bash -n harness/bin/teachclaw-omp
	node --test harness/tests/harness.test.mjs
	node harness/scripts/fresh-run-verifier.mjs \
		--baseline harness/examples/evidence-baseline.json \
		--final harness/examples/evidence-final.json \
		--scenario harness/examples/scenario.json \
		--out /tmp/public-teachclaw-verification.json >/dev/null
