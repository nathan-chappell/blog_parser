# Makefile

test:
	mypy .

index:
	python3 make_index.py

haystack:
	python3 haystack_client.py
