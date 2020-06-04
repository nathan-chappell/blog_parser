# Makefile

test: mypy_all test_parse2 test_processor
	#TEST=True python qa_index.py
	#TEST=True python3 qa_bot.py

mypy_all:
	mypy .

test_parse:
	python3 re_test.py
	mypy parser_base.py qa_parser.py
	TEST=True python3 qa_parser.py

test_parse2:
	python3 re2_test.py
	mypy parser_base.py qa_parser_2.py
	TEST=True python3 qa_parser_2.py

test_processor:
	mypy processor.py
	TEST=True python3 processor.py
