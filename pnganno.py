#!/usr/bin/env python

import sys
import os.path
from binascii import crc32

PROGNAME = os.path.split(sys.argv[0])[1]

MULT = [256 * 256 * 256,
        256 * 256,
        256,
        1]

PNG_HEADER = ['\x89', 'P', 'N', 'G', '\r', '\n', '\x1a', '\n']

def readBytes(s, n):
    """Read n bytes from stream s."""
    return [ s.read(1) for i in range(n) ]

def writeBytes(s, bts):
    for b in bts:
        s.write(b)

def readHeader(s):
    return readBytes(s, 8)

def readName(s):
    return s.read(4)

def intToBytes(x):
    b1 = x % 256
    x = x / 256
    b2 = x % 256
    x = x / 256
    b3 = x % 256
    b4 = x / 256
    return [chr(b4), chr(b3), chr(b2), chr(b1)]

def getKey(data):
    if "\x00" in data:
        p = data.index("\x00")
        return ("".join(data[:p]), p)
    else:
        return ("", -1)

class InvalidPNG(Exception):
    pass

class InvalidMode(Exception):
    pass

class Chunk(object):
    length = 0
    lenbytes = []
    tag = ""
    data = None
    crc = 0
    crcbytes = []
    key = ""                    # for tEXt chunks

    def readFromStream(self, s, data='all'):
        """Fill this chunk with data from stream `s'. If `data' is `all', 
always reads the data portion of the chunk. If `data' is `text', only
reads it for tEXt chunks. Otherwise, the data portion is skipped."""
        self.lenbytes = readBytes(s, 4)
        self.length = sum([ ord(self.lenbytes[i]) * MULT[i] for i in range(4) ])
        self.tag = readName(s)
        if data == 'all' or (data == 'text' and self.tag == 'tEXt'):
            self.data = readBytes(s, self.length)
            self.crcbytes = readBytes(s, 4)
            (key, p) = getKey(self.data)
            self.key = key
        else:
            s.seek(s.tell() + self.length + 4)

    def writeToStream(self, s):
        """Write this chunk to stream `s'."""
        writeBytes(s, self.lenbytes)
        s.write(self.tag)
        writeBytes(s, self.data)
        writeBytes(s, self.crcbytes)

class PNGfile(object):
    filename = ""
    header = []
    chunks = []
    endchunk = None
    valid = True
    
    def __init__(self, filename, data='all'):
        self.filename = filename
        sys.stderr.write("*** Reading PNG file {}\n".format(filename))
        with open(self.filename, "rb") as f:
            self.header = readHeader(f)
            if self.header != PNG_HEADER:
                raise InvalidPNG()
            while True:
                c = Chunk()
                c.readFromStream(f, data=data)
                if c.tag == 'IEND':
                    self.endchunk = c
                    break
                else:
                    self.chunks.append(c)

    def addTextChunk(self, key, text):
        c = None
        for w in self.chunks:
            if w.tag == 'tEXt' and w.key == key:
                c = w
                break
        if not c:
            c = Chunk()
            c.tag = 'tEXt'
            self.chunks.append(c)
            
        data = key + chr(0) + text
        c.data = data
        c.length = len(data)
        c.lenbytes = intToBytes(c.length)
        crc = crc32('tEXt')
        c.crc = crc32(data, crc) & 0xffffffff
        c.crcbytes = intToBytes(c.crc)
        return c
                    
    def writeToPNGfile(self, filename):
        sys.stderr.write("*** Writing image to PNG file {}\n".format(filename))
        with open(filename, "wb") as out:
            writeBytes(out, self.header)
            for c in self.chunks:
                c.writeToStream(out)
            self.endchunk.writeToStream(out)

class Main(object):
    infile = ""
    outfile = "/dev/stdout"
    textfile = ""
    mode = ""
    overwrite = False
    comments = []

    def setMode(self, m):
        if self.mode == "":
            self.mode = m
        elif self.mode == m:
            pass
        else:
            raise InvalidMode()
            
    def parseArgs(self, args):
        if "-h" in args or "--help" in args:
            return self.usage()
        prev = ""
        for a in args:
            if prev == '-a':
                self.setMode("add")
                self.comments.append(a)
                prev = ""
            elif prev == "-f":
                self.seTmode("addfile")
                self.textfile = a
                prev = ""
            elif prev == "-r":
                self.setMode("retrieve")
                parts = a.split(",")
                for k in parts:
                    self.comments.append(k)
                prev = ""
            elif prev == "-d":
                self.setMode("delete")
                self.comments.append(a)
                prev = ""
            elif prev == "-o":
                self.outfile = a
                prev = ""
            elif a in ["-a", "-r", "-o", "-f", "-d"]:
                prev = a
            elif a == "-O":
                self.overwrite = True
            elif a == "-D":
                self.setMode("dump")
            else:
                self.infile = a
        if self.infile:
            if os.path.isfile(self.infile):
                return True
            else:
                sys.stderr.write("ERROR: PNG file {} does not exist.\n".format(self.infile))
                return False
        else:
            return self.usage()

    def usage(self):
        sys.stdout.write("""{} - add or retrieve text comments in PNG files.

Usage: {} [options] PNGfile.png

Text comments consist of a `key' and its associated `text'. When called with no arguments,
this program displays the keys found in the PNG file, one per line. To add a new comment,
use the -a argument followed by a string of the form `key,text'. Note that multiple -a 
options can be supplied on the command line. If a key is already present in the PNG file,
its text will be overwritten with the supplied one. 

Comments can also be read from a file, specified with the -f option. This file should
be in tab-delimited format, with keys in the first column and text in the second one.
Lines starting with `#' or that do not contain at least two columns are ignored.

To delete one or more comments, use the -d option followed by one or more keys separated
by commas. Alternatively, multiple -d options can be supplied on the command line.

The three commands above generate a new PNG file that will be written to standard output, 
or to the file specified with the -o option. If -O is supplied instead, the program will 
overwrite the input PNG file.

To retrieve the text associated with one or more keys, use the -r option followed by the 
keys separated by commas. Alternatively, multiple -r options can be supplied on the command
line. The comments associated with the supplied keys, if present, will be written to the 
output in the order in which the keys appear on the command line, in the following format:

#key
text...

Results are printed to standard output or to the file specified with the -o option.

Options:

  -o O | Write output to file O. This will be a PNG file for the -a and -f commands.
  -a A | Add comment A to the PNG file. A should have the form key,text. This option
         can be repeated on the command line.
  -f F | Add comments reading them from file F. F should be tab-delimited with two
         columns containing key and text respectively.
  -r R | Retrieve the text associated with one or more keys R. For every key present in
         the PNG file, the corresponding text is printed to the output. Please note that
         the text may span more than one line. This option can be repeated on the command 
         line, or multiple keys can be supplied, separated by commas.
  -d D | Delete the text associated with key D.
  -O   | When using -a, -f, or -d, overwrite existing PNG file instead of writing new one.

Examples:

  # add two text entries to file image.png, writing new image to image2.png
  $ pngnote.py -a "key1,value for the first key" -a "key2,another comment" -o image2.png image.png

  # list keys now present in the image
  $ pngnote.py image2.png 
  key1
  key2

  # retrieve value for key1
  $ pngnote.py -r key1 image2.png
  #key1
  value for the first key

(c) 2020 A.Riva, ICBR Bioinformatics Core, University of Florida.

""".format(PROGNAME, PROGNAME))
        return False
    
    def run(self):
        sys.stderr.write("*** {}, (c) 2020\n".format(PROGNAME))
        if self.mode == "dump":
            self.dumpPNG()
        elif self.mode == "add":
            self.addText()
        elif self.mode == "addfile":
            self.addFile()
        elif self.mode == "retrieve":
            self.retrieve()
        elif self.mode == "delete":
            self.deleteText()
        elif self.mode == "":
            self.listKeys()

    def dumpPNG(self):
        P = PNGfile(self.infile, data=None)
        for c in P.chunks:
            sys.stdout.write("{} {}\n".format(c.tag, c.length))

    def savePNG(self, P):
        if self.overwrite:
            P.writeToPNGfile(self.infile)
        else:
            P.writeToPNGfile(self.outfile)
            
    def addText(self):
        P = PNGfile(self.infile)
        for w in self.comments:
            p = w.find(",")
            if p > 0:
                key = w[:p]
                text = w[p+1:]
                sys.stderr.write("*** {} => {}\n".format(key, text))
                P.addTextChunk(key, text)
        self.savePNG(P)
        
    def addFile(self):
        if not os.path.isfile(self.infile):
            sys.stderr.write("ERROR: file {} does not exist or is not readable.\n".format(self.infile))
            return
        P = PNGfile(self.infile)
        with open(self.textfile, "r") as f:
            for line in f:
                if line[0] == '#':
                    continue
                line = line.strip().split("\t")
                if len(line) > 1:
                    key = line[0]
                    text = line[1]
                    sys.stderr.write("*** {} => {}\n".format(key, text))
                    P.addTextChunk(key, text)
        self.savePNG(P)

    def listKeys(self):
        with open(self.outfile, "w") as out:
            P = PNGfile(self.infile, data='text')
            for c in P.chunks:
                if c.tag == 'tEXt':
                    out.write("{}\n".format(c.key))
        
    def retrieve(self):
        wanted = {}
        P = PNGfile(self.infile, data='text')
        for c in P.chunks:
            if c.tag == 'tEXt':
                (key, p) = getKey(c.data)
                if key in self.comments:
                    wanted[key] = "".join(c.data[p+1:])

        with open(self.outfile, "w") as out:
            for key in self.comments:
                if key in wanted:
                    out.write("#{}\n{}\n".format(key, wanted[key]))
        
    def deleteText(self):
        newchunks = []
        with open(self.outfile, "w") as out:
            P = PNGfile(self.infile)
            for c in P.chunks:
                if c.tag == 'tEXt':
                    (key, p) = getKey(c.data)
                    if key in self.comments:
                        sys.stderr.write("*** {} (deleted)\n".format(key))
                    else:
                        newchunks.append(c)
                else:
                    newchunks.append(c)    
        P.chunks = newchunks
        self.savePNG(P)
        
if __name__ == "__main__":
    M = Main()
    try:
        if M.parseArgs(sys.argv[1:]):
            M.run()
    except InvalidPNG as e:
        sys.stderr.write("ERROR: file {} is not a valid PNG file.\n".format(M.infile))
    except InvalidMode as e:
        sys.stderr.write("ERROR: only one of -a, -f, -d, or -r should be specified. Use -h for usage instructions.\n")
