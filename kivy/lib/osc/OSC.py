#!/usr/bin/python
#
# Open SoundControl for Python
# Copyright (C) 2002 Daniel Holth, Clinton McChesney
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
# For questions regarding this module contact
# Daniel Holth <dholth@stetson.edu> or visit
# http://www.stetson.edu/~ProctoLogic/
#
# Changelog:
# 15 Nov. 2001:
#   Removed dependency on Python 2.0 features.
#   - dwh
# 13 Feb. 2002:
#   Added a generic callback handler.
#   - dwh

import struct
import math
import sys
import string
import pprint


def hexDump(bytes):
    """Useful utility; prints the string in hexadecimal"""
    for i in range(len(bytes)):
        sys.stdout.write("%2x " % (ord(bytes[i])))
        if (i+1) % 8 == 0:
            print(repr(bytes[i-7:i+1]))

    if(len(bytes) % 8 != 0):
        print(string.rjust("", 11), repr(bytes[i-len(bytes)%8:i+1]))


class OSCMessage:
    """Builds typetagged OSC messages."""
    def __init__(self):
        self.address  = ""
        self.typetags = ","
        self.message  = ""

    def setAddress(self, address):
        self.address = address

    def setMessage(self, message):
        self.message = message

    def setTypetags(self, typetags):
        self.typetags = typetags

    def clear(self):
        self.address  = ""
        self.clearData()

    def clearData(self):
        self.typetags = ","
        self.message  = ""

    def append(self, argument, typehint = None):
        """Appends data to the message,
        updating the typetags based on
        the argument's type.
        If the argument is a blob (counted string)
        pass in 'b' as typehint."""

        if typehint == 'b':
            binary = OSCBlob(argument)
        else:
            binary = OSCArgument(argument)

        self.typetags = self.typetags + binary[0]
        self.rawAppend(binary[1])

    def rawAppend(self, data):
        """Appends raw data to the message.  Use append()."""
        self.message = self.message + data

    def getBinary(self):
        """Returns the binary message (so far) with typetags."""
        address  = OSCArgument(self.address)[1]
        typetags = OSCArgument(self.typetags)[1]
        return address + typetags + self.message

    def __repr__(self):
        return self.getBinary()

def readString(data):
    length   = string.find(data,"\0")
    nextData = int(math.ceil((length+1) / 4.0) * 4)
    return (data[0:length], data[nextData:])


def readBlob(data):
    length   = struct.unpack(">i", data[0:4])[0]
    nextData = int(math.ceil((length) / 4.0) * 4) + 4
    return (data[4:length+4], data[nextData:])


def readInt(data):
    if(len(data)<4):
        print("Error: too few bytes for int", data, len(data))
        rest = data
        integer = 0
    else:
        integer = struct.unpack(">i", data[0:4])[0]
        rest    = data[4:]

    return (integer, rest)



def readLong(data):
    """Tries to interpret the next 8 bytes of the data
    as a 64-bit signed integer."""
    high, low = struct.unpack(">ll", data[0:8])
    big = (int(high) << 32) + low
    rest = data[8:]
    return (big, rest)


def readDouble(data):
    """Tries to interpret the next 8 bytes of the data
    as a 64-bit double float."""
    floater = struct.unpack(">d", data[0:8])
    big = float(floater[0])
    rest = data[8:]
    return (big, rest)



def readFloat(data):
    if(len(data)<4):
        print("Error: too few bytes for float", data, len(data))
        rest = data
        float = 0
    else:
        float = struct.unpack(">f", data[0:4])[0]
        rest  = data[4:]

    return (float, rest)


def OSCBlob(next):
    """Convert a string into an OSC Blob,
    returning a (typetag, data) tuple."""

    if type(next) == type(""):
        length = len(next)
        padded = math.ceil((len(next)) / 4.0) * 4
        binary = struct.pack(">i%ds" % (padded), length, next)
        tag    = 'b'
    else:
        tag    = ''
        binary = ''

    return (tag, binary)


def OSCArgument(next):
    """Convert some Python types to their
    OSC binary representations, returning a
    (typetag, data) tuple."""

    if type(next) == type(""):
        OSCstringLength = math.ceil((len(next)+1) / 4.0) * 4
        binary  = struct.pack(">%ds" % (OSCstringLength), next)
        tag = "s"
    elif type(next) == type(42.5):
        binary  = struct.pack(">f", next)
        tag = "f"
    elif type(next) == type(13):
        binary  = struct.pack(">i", next)
        tag = "i"
    else:
        binary  = ""
        tag = ""

    return (tag, binary)


def parseArgs(args):
    """Given a list of strings, produces a list
    where those strings have been parsed (where
    possible) as floats or integers."""
    parsed = []
    for arg in args:
        print(arg)
        arg = arg.strip()
        interpretation = None
        try:
            interpretation = float(arg)
            if string.find(arg, ".") == -1:
                interpretation = int(interpretation)
        except:
            # Oh - it was a string.
            interpretation = arg
            pass
        parsed.append(interpretation)
    return parsed



def decodeOSC(data):
    """Converts a typetagged OSC message to a Python list."""
    table = { "i" : readInt, "f" : readFloat, "s" : readString, "b" : readBlob, "d" : readDouble }
    decoded = []
    address,  rest = readString(data)
    typetags = ""

    if address == "#bundle":
        time, rest = readLong(rest)
#       decoded.append(address)
#       decoded.append(time)
        while len(rest)>0:
            length, rest = readInt(rest)
            decoded.append(decodeOSC(rest[:length]))
            rest = rest[length:]

    elif len(rest) > 0:
        typetags, rest = readString(rest)
        decoded.append(address)
        decoded.append(typetags)
        if typetags[0] == ",":
            for tag in typetags[1:]:
                value, rest = table[tag](rest)
                decoded.append(value)
        else:
            print("Oops, typetag lacks the magic ,")

    return decoded


class CallbackManager:
    """This utility class maps OSC addresses to callables.

    The CallbackManager calls its callbacks with a list
    of decoded OSC arguments, including the address and
    the typetags as the first two arguments."""

    def __init__(self):
        self.callbacks = {}
        self.add(self.unbundler, "#bundle")

    def handle(self, data, source = None):
        """Given OSC data, tries to call the callback with the
        right address."""
        decoded = decodeOSC(data)
        self.dispatch(decoded, source)

    def dispatch(self, message, source = None):
        """Sends decoded OSC data to an appropriate calback"""
        try:
            if type(message[0]) == str :
                # got a single message
                address = message[0]
                self.callbacks[address](message, source)

            elif type(message[0]) == list :
                # smells like nested messages
                for msg in message :
                    self.dispatch(msg, source)

        except KeyError as e:
            # address not found
            print('address %s not found ' % address)
            pprint.pprint(message)
        except IndexError as e:
            print('got malformed OSC message')
            pass
        except None as e:
            print("Exception in", address, "callback :", e)

        return

    def add(self, callback, name):
        """Adds a callback to our set of callbacks,
        or removes the callback with name if callback
        is None."""
        if callback == None:
            del self.callbacks[name]
        else:
            self.callbacks[name] = callback

    def unbundler(self, messages):
        """Dispatch the messages in a decoded bundle."""
        # first two elements are #bundle and the time tag, rest are messages.
        for message in messages[2:]:
            self.dispatch(message)








if __name__ == "__main__":
    hexDump("Welcome to the OSC testing program.")
    print()
    message = OSCMessage()
    message.setAddress("/foo/play")
    message.append(44)
    message.append(11)
    message.append(4.5)
    message.append("the white cliffs of dover")
    hexDump(message.getBinary())

    print("Making and unmaking a message..")

    strings = OSCMessage()
    strings.append("Mary had a little lamb")
    strings.append("its fleece was white as snow")
    strings.append("and everywhere that Mary went,")
    strings.append("the lamb was sure to go.")
    strings.append(14.5)
    strings.append(14.5)
    strings.append(-400)

    raw  = strings.getBinary()

    hexDump(raw)

    print("Retrieving arguments...")
    data = raw
    for i in range(6):
        text, data = readString(data)
        print(text)

    number, data = readFloat(data)
    print(number)

    number, data = readFloat(data)
    print(number)

    number, data = readInt(data)
    print(number)

    hexDump(raw)
    print(decodeOSC(raw))
    print(decodeOSC(message.getBinary()))

    print("Testing Blob types.")

    blob = OSCMessage()
    blob.append("","b")
    blob.append("b","b")
    blob.append("bl","b")
    blob.append("blo","b")
    blob.append("blob","b")
    blob.append("blobs","b")
    blob.append(42)

    hexDump(blob.getBinary())

    print(decodeOSC(blob.getBinary()))

    def printingCallback(*stuff):
        sys.stdout.write("Got: ")
        for i in stuff:
            sys.stdout.write(str(i) + " ")
        sys.stdout.write("\n")

    print("Testing the callback manager.")

    c = CallbackManager()
    c.add(printingCallback, "/print")

    c.handle(message.getBinary())
    message.setAddress("/print")
    c.handle(message.getBinary())

    print1 = OSCMessage()
    print1.setAddress("/print")
    print1.append("Hey man, that's cool.")
    print1.append(42)
    print1.append(3.1415926)

    c.handle(print1.getBinary())

    bundle = OSCMessage()
    bundle.setAddress("")
    bundle.append("#bundle")
    bundle.append(0)
    bundle.append(0)
    bundle.append(print1.getBinary(), 'b')
    bundle.append(print1.getBinary(), 'b')

    bundlebinary = bundle.message

    print("sending a bundle to the callback manager")
    c.handle(bundlebinary)
