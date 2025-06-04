import sys
import py

DEBUG = True
ROOT = py.path.local(__file__).join('..', '..')

# we want an option to select between "sagra" mode and "ristorante" mode.
# In sagra mode:
#     - INCLUDE_ZENEIZE = False (but we need to fix it)
#     - the food receipt should be slightly different: order num should be BIG

MODE = 'sagra'
#MODE = 'ristorante'
