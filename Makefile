# Makefile

test:
	mypy blog_parser.py
	mypy paragraph.py
	mypy paragraph_stats.py
	mypy machine_html_parser.py

run:
	python3 blog_parser.py
