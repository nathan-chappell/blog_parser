# Makefile

test:
	mypy blog_parser.py
	mypy paragraph.py
	mypy paragraph_stats.py

run:
	python3 blog_parser.py
