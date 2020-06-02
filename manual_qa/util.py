# util.py

import os

def is_test(): return os.environ.get('TEST',False)

