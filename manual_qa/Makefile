# Makefile

test:
	mypy .
	python3 test.py
	TEST=True python3 qa_parser.py
	#TEST=True python qa_index.py
	TEST=True python3 processor.py
	TEST=True python3 qa_bot.py
