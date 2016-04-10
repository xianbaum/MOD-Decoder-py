import moddecoder
import sys

if len(sys.argv) != 2:
    print("No file specified")
else:
    mod = moddecoder.openmodfile( sys.argv[1])
    moddecoder.print_headers( mod )
    moddecoder.print_all_sample_headers( mod )
