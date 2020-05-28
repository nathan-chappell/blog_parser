# Makefile

test:
	mypy .
	python3 test_samples.py
	EXPERIMENTS_TEST=True python3 experiments.py
	python3 experiments_analysis.py

run:
	python3 test_samples.py
	python3 experiments.py
	python3 experiments_analysis.py

index:
	python3 make_index.py

haystack:
	python3 haystack_client.py
