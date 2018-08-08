# this is needed to 'import server' from the mobile/ tests
import sys
import py
DIR = py.path.local(__file__).dirpath()
ROOT = DIR.join('..', '..')
sys.path.insert(0, str(ROOT))
