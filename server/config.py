import sys
import py

DEBUG = True
ROOT = py.path.local(__file__).join('..', '..')


MODE = 'sagra'
#MODE = 'ristorante'

# *** MODE == 'sagra' ***
#
# If the order contains only Zeneize and drinks, it is considered "Fila A".
# "Fila A" orders are NOT sent to the food printer.
#
# "Fila B" orders are sent to the food printer. The food receipt includes:
#   - Focaccini Zeneize (if present)
#   - Other focaccini
#   - Other food (e.g. brace)
#   - Drinks are NOT printed on this receipt

# *** MOE == 'ristorante' ***
#
# There is no concept of Fila A and Fila B: if the order contain any food, it
# is always sent to the food printer. In this mode, drinks ARE included.
