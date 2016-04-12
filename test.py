import moddecoder
import sys

if len(sys.argv) != 2:
    print("No file specified")
else:
    mod = moddecoder.open_mod( sys.argv[1])
    moddecoder.print_sample_headers( mod)
    moddecoder.print_pattern( mod, 0)
    moddecoder.alsaplay(mod)
