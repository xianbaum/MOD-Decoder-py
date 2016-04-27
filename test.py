import pymodtracker
import sys

if len(sys.argv) != 2:
    print("No file specified")
else:
    mod = pymodtracker.open_mod( sys.argv[1])
    pymodtracker.print_sample_headers( mod)
    pymodtracker.print_pattern( mod, 0)
    pymodtracker.alsaplay(mod)
