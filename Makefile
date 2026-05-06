PYTHON ?= python3
export PYTHONPYCACHEPREFIX ?= /tmp/knowledge-agent-pyc

.PHONY: compile lint test test-embedding doctor init-db run-app benchmark benchmark-live harness harness-live check

compile:
	$(PYTHON) -m compileall -q src tests app.py import_csv.py mcp_servers data/init_db.py

lint:
	PYTHON=$(PYTHON) scripts/lint.sh

test:
	PYTHON=$(PYTHON) scripts/test.sh

test-embedding:
	RUN_EMBEDDING_TESTS=1 PYTHON=$(PYTHON) scripts/test.sh -m embedding

doctor:
	$(PYTHON) -m src.doctor

init-db:
	PYTHON=$(PYTHON) scripts/init_db.sh

run-app:
	PYTHON=$(PYTHON) scripts/run_app.sh

benchmark:
	$(PYTHON) -m src.eval.benchmark --output data/benchmark_report.md

benchmark-live:
	$(PYTHON) -m src.eval.benchmark --live --output data/benchmark_report.md

harness:
	$(PYTHON) -m src.harness.cli --output data/harness_report.md

harness-live:
	$(PYTHON) -m src.harness.cli --live --output data/harness_report.md

check: lint test
