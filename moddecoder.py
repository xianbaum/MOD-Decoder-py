import sys
import binascii
import struct
import re
from base64 import b16encode

try:
    from tabulate import tabulate
except ImportError:
    pass

class Mod:
    class Sample:
        def __init__(self):
            self.name = ""
            self.size = 0
            self.finetune = 0
            self.volume = 0
            self.repeat_point = 0
            self.repeat_len = 0
            self.data = None
    class Pattern:
        class Channel:
            class Tick:
                def __init__(self):
                    self.note = None
                    self.sample = None
                    self.effect = None
            def __init__(self):
                self.tick = [None]*64
                for i in range(0, 64):
                    self.tick[i] = Mod.Pattern.Channel.Tick()
        def __init__(self):
            self.channel = []
    def __init__(self):
        self.filename = ""
        self.title = ""
        self.song_length = 0
        self.restart_byte = 127
        self.signature = None
        self.sample = [None]*31
        self.channel_count = 4 #Not sure how to find channel count
        self.pattern = []
        self.pattern_sequences = [None]*128
        for i in range(0, 31):
            self.sample[i] = Mod.Sample()
        
def open_mod( filename ):
    def get_sample_headers( mod, f ):
        for i in range( 0, 31): #31, not 32
            # 30 bytes all together for each sample header
            sample_struct = struct.unpack("22sHbcHH",f.read(30))
            mod.sample[i].name = sample_struct[0].decode("utf-8")
            mod.sample[i].size = sample_struct[1]
            print(mod.sample[i].size)
            mod.sample[i].finetune = (sample_struct[2] if sample_struct[2] < 8 else sample_struct[2] - 16)
            mod.sample[i].volume = ord(sample_struct[3])
            mod.sample[i].repeat_point = sample_struct[4]
            mod.sample[i].repeat_len = sample_struct[5]

    def get_pattern_headers( mod, f ):
        header_struct = struct.unpack("130c4s",f.read(134))
        mod.song_length = ord(header_struct[0])
        mod.pattern = []
        mod.restart_byte = ord(header_struct[1])
        for i in range( 0, 128):
            mod.pattern_sequences[i] = ord(header_struct[2+i])
        try:
            mod.signature = header_struct[130].decode("utf-8")
            interpret_signature( mod, f)
        except UnicodeDecodeError: #Pattern data started already
            #TODO: test for 15 sample MOD
            f.seek(-4,1)
            
    def get_patterns( mod, f):
        for p in range(0, mod.song_length):
            mod.pattern.append(Mod().Pattern())
            for c in range(0, mod.channel_count):
                mod.pattern[p].channel.append(Mod.Pattern.Channel())
            for t in range(0, 64):
                for c in range(0, mod.channel_count):
                    thex = binascii.hexlify(struct.unpack("4s",f.read(4))[0])
                    mod.pattern[p].channel[c].tick[t].note=thex[1:4]
                    mod.pattern[p].channel[c].tick[t].sample=thex[0:1]+thex[4:5]
                    mod.pattern[p].channel[c].tick[t].effect=thex[5:8]
    def get_samples( mod, f):
        for i in range(0, 31): #correct as far as i know?
            if mod.sample[i].size > 0:
                mod.sample[i].data = f.read(mod.sample[i].size)

    def interpret_signature( mod, f ):
        if mod.signature == "M.K." or mod.signature == "M!K!" or mod.signature == "M&K!": #most common
            return
        elif mod.signature[1:4] == "CHN": #4CHN - 9CHN channels
            mod.channel_count = int(mod.signature[0:1])
        elif mod.signature[2:4] == "CH" or mod.signature[2:4] == "CN":
            mod.channel_count = int(mod.signature[0:2])
        elif mod.signature[0:3] == "TDZ":
            mod.channel_count = int(mod.signature[3:4])
        elif mod.signature[0:3] == "FLT":
            mod.channel_count = int(mod.signature[3:4])
        elif mod.signature == "CD81" or mod.signature == "OKTA" or mod.signature == "OCTA":
            mod.channel_count = 8
        elif re.search("[a-z][A-Z]",mod.signature):
                return
        #TODO: test for 15 sample MOD
        f.seek(-4,1)

    def interpret_note( note ):
        pass

    with open( filename, "rb", 16 ) as f:
        mod = Mod()
        mod.filename = filename
        #20 bytes for title padded with null bytes b2a_uu adds a newline...
        mod.title = struct.unpack("20s",f.read(20))[0].decode("utf-8")
        get_sample_headers( mod, f)
        #Byte 950 here
        get_pattern_headers( mod, f)
        #Byte 1084 here; begin patterns
        get_patterns( mod, f)
        #Byte xxxx (could be any size) here; begin sample data
        get_samples( mod, f)
        return mod

def print_sample_header( sample ):
    print("Sample name: {}".format(sample.name))
    print("Size       : {}".format(sample.size))
    print("Data actual: {}".format(sys.getsizeof(sample.data)))
    print("Finetune   : {}".format(sample.finetune))
    print("Volume     : {}".format(sample.volume))
    print("Repeat pt. : {}".format(sample.repeat_point))
    print("Repeat len.: {}".format(sample.repeat_len))
    
def print_sample_headers( mod ):
    for i in range(0, 31):
         print("Sample {}".format(i))
         print_sample_header( mod.sample[i])
    
def print_header( mod ):
    print("Filename   : {}".format(mod.filename))
    print("Title      : {}".format(mod.title))
    print("Restartbyte: {}".format(mod.restart_byte))
    print("Signature  : {}".format(mod.signature))
    print("Song Length: {}".format(mod.song_length))
    print("Channlcount: {}".format(mod.channel_count))
    print("Patterns   : {}".format(mod.pattern_sequences[0:mod.song_length]))

def hex2str( hex ):
    return bin(ord("\'")).split('b')[1]

def print_comments( mod ):
    for i in range(0, 31):
        print(mod.sample[i].name)

#requires tabulate
def print_pattern( mod, no ):
    table = [None]*64
    channel_header = []
    for t in range(0, 64):
        table[t] = [None]*mod.channel_count
        for c in range(0, mod.channel_count):
            data = "{} {} {} ".format(
                mod.pattern[no].channel[c].tick[t].note.decode("utf-8"),
                mod.pattern[no].channel[c].tick[t].sample.decode("utf-8"),
                mod.pattern[no].channel[c].tick[t].effect.decode("utf-8"))
            table[t][c] = data
    for c in range(0, mod.channel_count ):
        channel_header.append( "Channel {}".format(c))
    print (tabulate(table, channel_header, "fancy_grid" ))
