import sys
import binascii
import struct

class Mod:
    class Sample:
        name = ""
        size = 0
        finetune = 0
        volume = 0
        repeat_point = 0
        repeat_len = 0
        data = ""
        #not sure whether I should use the default struct or use a class
        struct = None
    filename = ""
    title = ""
    song_length = 0
    restart_byte = 127
    signature = ""
    pattern_sequences = [None]*128
    sample = [None]*31

def openmodfile( filename ):
    def get_sample_headers( mod, f ):
        for i in range( 0, 31): #31, not 32
            mod.sample[i] = Mod.Sample()
            # 30 bytes all together for each sample header
            sample_struct = struct.unpack("22sHccHH",f.read(30))
            mod.sample[i].name = sample_struct[0].decode("utf-8")
            mod.sample[i].size = sample_struct[1]
            mod.sample[i].finetune = ord(sample_struct[2])
            mod.sample[i].volume = ord(sample_struct[3])
            mod.sample[i].repeat_point = sample_struct[4]
            mod.sample[i].repeat_len = sample_struct[5]

    def get_pattern_headers( mod, f ):
        header_struct = struct.unpack("130c4s",f.read(134))
        mod.song_length = ord(header_struct[0])
        mod.restart_byte = ord(header_struct[1])
        for i in range( 0, 128):
            mod.pattern_sequences[i] = ord(header_struct[2+i])
        mod.signature = header_struct[130].decode("utf-8")

    with open( filename, "rb", 16 ) as f:
        mod = Mod()
        mod.filename = filename
        #20 bytes for title padded with null bytes b2a_uu adds a newline...
        mod.title = struct.unpack("20s",f.read(20))[0].decode("utf-8")
        get_sample_headers( mod, f)
        #Byte 950 here
        get_pattern_headers( mod, f)
        #Byte 1084 here; begin patterns
        #Byte xxxx (could be any size) here; begin sample data
        return mod

def print_sample_header( sample ):
    print("Sample name: {}".format(sample.name))
    print("Size       : {}".format(sample.size))
    print("Finetune   : {}".format(sample.finetune))
    print("Volume     : {}".format(sample.volume))
    print("Repeat pt. : {}".format(sample.repeat_point))
    print("Repeat len.: {}".format(sample.repeat_len))

def print_all_sample_headers( mod ):
    for i in range(0, 31):
         print("Sample {}".format(i))
         print_sample_header( mod.sample[i])
    
def print_headers( mod ):
    print("Filename   : {}".format(mod.filename))
    print("Title      : {}".format(mod.title))
    print("Restartbyte: {}".format(mod.restart_byte))
    print("Signature  : {}".format(mod.signature))
    print("Song Length: {}".format(mod.song_length))
    print("Patterns   : {}".format(mod.pattern_sequences))
