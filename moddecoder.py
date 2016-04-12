import binascii
import struct
import re
from base64 import b16encode
import time

#for print_pattern
try:
    from tabulate import tabulate
except ImportError:
    pass

#for alsaplay
try:
    import alsaaudio
except ImportError:
    pass

class Mod:
    class Sample:
        def __init__(self):
            self.name = ""
            self.size = 0
            self.finetune = 0
            self.volume = 0
            self.repeat_pos = 0
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
        self.channel_count = 4
        self.pattern = []
        self.pattern_sequences = [None]*128
        for i in range(0, 31):
            self.sample[i] = Mod.Sample()
        self.sample_count = 31

class Player:
    class Channel:
        def __init__(self):
            self.sample = 0
            self.volume = 64
            self.effect = 0
            self.sample_pos = 0
            self.last_time = time.time()
        def read_tick( self, tick ):
            num = int( tick.note.decode("utf-8"), 16 )
            if tick.note is not 0:
                self.note = num
                self.sample_pos = 0
            if tick.sample is not 0 and tick.sample is not self.sample:
                self.instrument = tick.sample
                self.sample_pos = 0
            if tick.effect is not 0 and tick.effect is not self.effect:
                self.effect = tick.effect

    def sound_data_from_channel( self, channel_num, mod ):
        chan = self.channel[channel_num]
        sample = mod.sample[ chan.sample ]
        if mod.sample[ chan.sample ].data:
            temp_last_time = chan.last_time
            chan.last_time = time.time()
            elapsed_time = chan.last_time - temp_last_time
            bytes_amount = round(self.clock/chan.note*elapsed_time)
            if sample.repeat_pos is not 0 and sample.repeat_len is not 256 and  chan.sample_pos+bytes_amount > sample.repeat_pos + sample.repeat_len:
                tmp_bytes = sample.repeat_pos+ sample.repeat_len - chan.pos + bytes_amount
                return_data = sample.data[ chan.sample_pos : sample.repeat_pos + sample.repeat_len] + sample.data[ sample.repeat_pos : sample.repeat_pos + tmp_bytes ]
                chan.sample_pos = sample.repeat_pos + tmp_bytes
                return return_data
            elif chan.sample_pos > sample.size:
                bytes_amount = sample.size -chan.sample_pos
                return_data = sample.data[ chan.sample_pos : chan.sample_pos + bytes_amount]
                sample_pos = sample.size
                return return_data
            return_data = sample.data[ chan.sample_pos : chan.sample_pos + bytes_amount ]
            chan.sample_pos += bytes_amount
            return return_data
        return b'\x00'

    def __init__(self, channels, clock_rate = 7159090.5): #7093789.2 for PAL
        self.clock = clock_rate
        self.channel_count = channels
        self.channel = [None]*channels
        for i in range(0, channels):
            self.channel[i] = Player.Channel()
        self.pattern_num = 0
        self.sample_pos = 0




def open_mod( filename ):
    def get_sample_headers( mod, f ):
        for i in range( 0, mod.sample_count):
            # 30 bytes all together for each sample header
            sample_struct = struct.unpack("22s2sbcHH",f.read(30))
            mod.sample[i].name = sample_struct[0].decode("utf-8")
            mod.sample[i].size = int.from_bytes(sample_struct[1], byteorder="big")*2
            mod.sample[i].finetune = (sample_struct[2] if sample_struct[2] < 8 else sample_struct[2] - 16)
            mod.sample[i].volume = ord(sample_struct[3])
            mod.sample[i].repeat_pos = sample_struct[4]
            mod.sample[i].repeat_len = sample_struct[5]

    def get_pattern_headers( mod, f ):
        header_struct = struct.unpack("130c4x",f.read(134)) #already read last 4
        mod.song_length = ord(header_struct[0])
        mod.pattern = []
        mod.restart_byte = ord(header_struct[1])
        for i in range( 0, 128):
            mod.pattern_sequences[i] = ord(header_struct[2+i])
            
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
        for i in range(0, mod.sample_count):
            if mod.sample[i].size > 0:
                mod.sample[i].data = f.read(mod.sample[i].size)

    def read_signature( mod, f ):
        f.seek(1080)#where the M.K. initials are
        siggy = f.read(4)
        try:
            mod.signature = siggy.decode("utf-8")
        except UnicodeDecodeError: #if gibberish, then it's a 15 sample MOD
            mod.sample_count = 15
            mod.sample = mod.sample[:15]
            f.seek(0,0)
            return
        if mod.signature == "M.K." or mod.signature == "M!K!" or mod.signature == "M&K!": #most common
            pass
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
        elif re.search("[a-z][A-Z]",mod.signature): #does it have any letters?
            pass
        else:
            mod.sample_count = 15
            mod.sample = mod.sample[:15]
        f.seek(0,0)

    with open( filename, "rb", 16 ) as f:
        mod = Mod()
        mod.filename = filename
        #We check these bytes at the beginning to see if it's a 15 sample MOD
        read_signature( mod, f)
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
    print("Finetune   : {}".format(sample.finetune))
    print("Volume     : {}".format(sample.volume))
    print("Repeat pos : {}".format(sample.repeat_pos))
    print("Repeat len : {}".format(sample.repeat_len))
    
def print_sample_headers( mod ):
    for i in range(0, mod.sample_count):
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
    for i in range(0, mod.sample_count):
        print(mod.sample[i].name)

def printable_note( note_in_hex ):
    decoded = note_in_hex.decode("utf-8")
    num = int( decoded, 16 )
    if num == 0:
        return "---"
    tone_list = [1712, 1616, 1525, 1440, 1357, 1281, 1209,1141,1077,1017, 961, 907,856, 808, 762, 720, 678, 640, 604, 570, 538, 508, 480, 453,428, 404, 381, 360, 339, 320, 302, 285, 269, 254, 240, 226,214, 202, 190, 180, 170, 160, 151, 143, 135, 127, 120, 113,1712,1616,1525,1440,1357,1281,1209,1141,1077,1017, 961, 907,107, 101,  95,  90,  85,  80,  76,  71,  67,  64,  60,  57]
    note_list = ["C ", "C#", "D ", "D#", "E ", "F ", "F#", "G ", "G#", "A ", "A#", "B "]
    for i in range(0, len(tone_list)):
        if num == tone_list[i]:
            if i > 12:
                octave_note = divmod(i, 12)
            else:
                octave_note = [0, 12-i]
            return "{}{}".format( note_list[octave_note[1]], octave_note[0]+3)
    #Manually tuned. No note
    return decoded

def printable_sample( sample_in_hex ):
    sample_num = sample_in_hex.decode("utf-8")
    num = int( sample_num, 16 )
    if num == 0:
        return "--"
    return "{}".format(sample_num)

def printable_effect( effect ):
    decoded = effect.decode("utf-8").upper()
    if decoded == "000":
        return "---"
    return decoded

#requires tabulate
def print_pattern( mod, no ):
    table = [None]*64
    channel_header = []
    for t in range(0, 64):
        table[t] = [None]*mod.channel_count
        for c in range(0, mod.channel_count):
            data = "{} {} {} ".format(
                printable_note(mod.pattern[no].channel[c].tick[t].note),
                printable_sample(mod.pattern[no].channel[c].tick[t].sample),
                printable_effect(mod.pattern[no].channel[c].tick[t].effect))
            table[t][c] = data
    for c in range(0, mod.channel_count ):
        channel_header.append( "Channel {}".format(c))
    print (tabulate(table, channel_header, "fancy_grid" ))

#Requires alsaaudio
def alsaplay( mod ):
    player = Player( mod.channel_count )
    player.channel[0].read_tick(mod.pattern[0].channel[0].tick[0])
    out = alsaaudio.PCM(alsaaudio.PCM_PLAYBACK)
    out.setchannels(1)
    out.setrate(8000)
    out.setformat(alsaaudio.PCM_FORMAT_S16_LE)
    while True:
        j = player.sound_data_from_channel( 0, mod )
        out.setperiodsize( int(mod.pattern[0].channel[0].tick[0].note.decode("utf-8"), 16))
        print(j)
        out.write(j)
