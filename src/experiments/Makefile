# Makefile

test:
	mypy .
	EXPERIMENTS_TEST=true python3 test_samples.py
	EXPERIMENTS_TEST=true python3 baseline.py
	EXPERIMENTS_TEST=true python3 experiments.py
