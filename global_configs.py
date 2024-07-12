import sys
import os

ROOT_DIR = os.path.abspath(__file__)
for _ in range(2):
    ROOT_DIR = os.path.dirname(ROOT_DIR)

if not ROOT_DIR in sys.path:
    sys.path.append(ROOT_DIR)
