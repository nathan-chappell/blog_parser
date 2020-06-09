# Makefile

classfier: mypy_all
	python3 classifier.py

test: mypy_all test_parse2 test_index
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

test_index:
	mypy index.py
	TEST=True python3 index.py
