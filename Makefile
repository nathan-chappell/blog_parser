# Makefile

test:
	mypy blog_parser.py
	mypy paragraph.py

run:
	python3 blog_parser.py
