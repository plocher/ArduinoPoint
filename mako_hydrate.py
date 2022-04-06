#!/bin/env python3

# rehydrate a control point from XML
# TODO: Add sections/section with list of TCs to aggregate

__author__  = 'plocher'
__version__ = '0.2'

from lxml import etree
import argparse, sys, os
import datetime
import collections
import pprint
from io import StringIO
import re
from natsort import natsorted

from mako.template import Template

pp = pprint.PrettyPrinter(indent=4)


#
# We have an XML file that defines a control point, both logically and physically
#
# The logical part consists of the code line CONTROLS and INDICATIONS
# They map to a structure made up of track circuits, switches, signals and maintainer calls
#
# The physical mappings are to the ctc panels, local control panels and the field units
# and their connections to the layout hardware
#
# The XML file captures this as explicit bit definitions for indications, controls and field
# arrays of bits.  The names of the various items are used to tie things together
# (i.e. INDICATION "1NW", CONTROL "1NW", field "1NW" and SWITCH "1" normal="1NW" are related
# explicitly by name or attribute
#

# Reading an XML file creates a set of objects that are used to represent these linkages:
#
# ControlPoint - ties a single CP together; there are multiple CPs on a layout
#
# Appliances:  - the appliances found at a CP
#   Switch
#   Signal
#   SignalMastHead
#   Maintainer
#   TrackCircuit
#
# Collections: - the bit mappings used to communicate to/from/within a CP
#   Indications
#   Controls
#   Field
#   Panel

class SimpleList(object):
    def __init__(self, cpname, fieldname, mytype):
        self.mytype    = mytype
        self.cpname    = cpname
        self.fieldname = fieldname
        self.children  = {}

    def add(self, child, list = None):
        if list is None:
            list = self.children
        if child.name not in list:
            list[child.name] = child
            # print("Add: {} {}: child: {}".format(self.mytype, self.fieldname, child.toString()))
        else:
            print("Error: {} {}: Can not add a duplicate child: {}".format(self.mytype, self.fieldname, child.toString()))

    def __str__(self):
        s = "{blank:<{indent}}{type:<8}: cp: {cpname} children: {num}".format(blank='', indent=indent, type=self.mytype,
                                                                              cpname=self.cpname,
                                                                              num=len(self.children))
        for k, v in self.children.items():
            cs = ''
            try:
                cs = v.toString()
            except AttributeError:
                cs = 'child has no toString() method'
            s = s + '\n' + cs
        return s

    def toString(self, indent=0):
        return str(self)

    def totext(self):
        s=''
        for k,v in self.children.items():
            cs = ''
            try:
                cs = v.totext()
            except AttributeError:
                try:
                    cs += v.toString()
                except AttributeError:
                    cs += 'child has no totext() or toString() method'
            s = s + '\n\t' + cs
        return s

    def towiki(self):
        s = ''
        for k, v in self.children.items():
            cs = ''
            try:
                cs = v.towiki()
            except AttributeError:
                try:
                    cs += v.toString()
                except AttributeError:
                    cs += 'child has no towiki() or toString() method'
            s = s + '\n\t' + cs
        return s

    def sort(self):
        for k, v in self.children.items():
            try:
                v.sort()
            except AttributeError:
                pass

    def generate(self):
        print('calling {}.generate()'.format(self.mytype))
        for k, v in self.children.items():
            print('    child: {} {}'.format(v.mytype, v.name))
            try:
                v.generate()
            except AttributeError:
                pass

class SimpleNamedList(SimpleList):
    def __init__(self, cpname, xml):
        self.name = xml.attrib.get("name")
        super(SimpleNamedList, self).__init__(cpname, self.name, "SimpleNamedList")

    def toString(self, indent=0):
        s = super(SimpleNamedList, self).toString()
        s += "{blank:<{indent}}name: {name}".format(blank='', indent=indent, name=self.name)
        return s

    def towiki(self):
        return self.toString()


    def totext(self):
        return self.toString()

class SimpleNamedTypedList(SimpleList):
    def __init__(self, cpname, name, mytype): # was (...cpname, mytype, name...)
        super(SimpleNamedTypedList, self).__init__(cpname, name, mytype)
        self.name = name

    def toString(self, indent=0):
        s = super(SimpleNamedTypedList, self).toString()
        s += "{blank:<{indent}}name: {name}".format(blank='', indent=indent, name=self.name)
        return s

    def towiki(self):
        return self.toString()


    def totext(self):
        return self.toString()

class IOCollection(SimpleNamedTypedList):
    def __init__(self, cpname, fieldname, mytype, num):
        super(IOCollection, self).__init__(cpname, fieldname,  mytype)
        self.num       = num
        self.bits      = 8
        self.units     = 'Byte'
        self.table     = [[0 for x in range(self.bits+1)] for y in range(self.num+1)]
        self.endat     = self.num;

    def add(self, child, list = None):
        super(IOCollection, self).add(child, list)
        #print("IOCollection.Add [{}, {}] {}\n".format(self.bits, self.num, child.toString()))
        self.table[child.device][child.bit] = child.name + child.suffix

    def sort(self):
        d = dict(sorted(self.children.items(), key=lambda item: item[1]))
        self.children = d
        self.endat = self.num
        for device in range(self.num - 1, -1, -1):
            used = False
            for bit in range(self.bits):
                v = self.table[device][bit]
                if (not isinstance(v, int)):
                    used = True
            if used:
                self.endat = device
                break

        if (self.endat + 1) < self.num:
            self.endat = self.endat + 1

    '''
    print out contents of self.table[device][bit] with a variable output format

    heading
    tBegin
    prepend
        "bit _########_"
        prepend2
        x self.bits
    postpend
    _devicename_
    prepend3
        _value_
        prepend4
        x self.bits
    postpend2
    tEnd
    '''
    def tableGenerator(self, heading, tBegin, prepend, prepend2, postpend, devname, prepend3, prepend4, postpend2, tEnd, fmt8):
        hold = self.num
        self.num = self.endat

        output = StringIO()
        output.write(heading)
        output.write(tBegin)
        for bit in range(self.bits):
            output.write(prepend)
            prepend = prepend2
            v = 'bit ' + str(bit)
            output.write('{:8}'.format(v))
        output.write(postpend)

        for device in range(self.num):
            output.write(devname.format(str(device)))
            prepend = prepend3
            for bit in range(self.bits):
                output.write(prepend)
                prepend = prepend4
                v = self.table[device][bit]
                if (isinstance(v, int)):
                    v = '- - -'
                if (len(v) > 2) and (v[1] == '_') and ((v[0] == 'I') or (v[0] == 'O')):
                    v = v[:1].lower() + ' ' + v[2:]
                output.write(fmt8.format(v))
            output.write(postpend2)
        output.write(tEnd)
        contents = output.getvalue()
        output.close()
        self.num = hold
        return contents


    def towiki(self):
        heading  = '\n<table border=1 style="font-family: monospace;width: 80%;">\n<tr>\n<th colspan="{}"> {} for {}\n</th>\n</tr>\n'.format(self.bits + 1, self.mytype, self.cpname)
        tBegin   ='\n'
        prepend  = '\n<tr>\n<th> {}\n</th>\n<td align="center">'.format(self.units)
        prepend2 = '\n</td>\n<td align="center"> '
        postpend = '\n</td>\n</tr>\n'
        devname  = '\n<tr>\n<th> {:<2}\n</th>  '
        prepend3 = '\n<td align="center"> '
        prepend4 = '\n</td>\n<td align="center"> '
        postpend2= '\n</td>\n</tr>\n'
        tEnd     = '\n</table>\n'
        fmt8     = '{:<8}'

        return self.tableGenerator(heading, tBegin, prepend, prepend2, postpend, devname, prepend3, prepend4, postpend2, tEnd, fmt8)


    def totext(self):
        heading  = '          {} for {}\n'.format(self.mytype, self.cpname)
        tBegin   = '          +'
        for x in range(0,self.bits):
            tBegin = tBegin + '---------+'
        tBegin = tBegin + '\n'
        prepend  = '          | '
        prepend2 = '| '
        postpend = '|\n' + tBegin
        devname  = '  Byte {:>2} | '
        prepend3 = ''
        prepend4 = '| '
        postpend2= '|\n'
        tEnd     = tBegin
        fmt8     = '{:<8}'
        return self.tableGenerator(heading, tBegin, prepend, prepend2, postpend, devname, prepend3, prepend4, postpend2, tEnd, fmt8)

class IOData(object):
    def __init__(self, cpname, fieldname, mytype, name, suffix, device, bit):
        self.cpname   = cpname
        self.fieldname=fieldname
        self.mytype   = mytype
        self.name     = name
        self.suffix   = suffix
        self.device   = int(device, 0)
        self.bit      = int(bit, 0)
        self.fieldvalue = 'ID({:d}, {:d})'.format(self.device, self.bit)
        if fieldname is not None:
            #self.fullname   = '{}_{}_{}'.format(self.cpname, self.fieldname, self.name)
            #self.fullname   = '{}_F{}'.format(self.cpname, self.name)
            self.fullname = '{cpname}_{name}{flag}'.format(cpname=self.cpname, name=self.name, flag=self.suffix)
        else:
            #self.fullname = '{}_F{}'.format(self.cpname, self.name)
            self.fullname = '{cpname}_{name}{flag}'.format(cpname=self.cpname, name=self.name, flag=self.suffix)

    def toString(self, indent=0):
        return "{blank:<{indent}}{mytype:<8}: cp: {cpname} field: {fieldname} name: {name} dev: {dev:<2} bit: {bit:<2} suffix: {suf:<2}".format(
            blank='', indent=indent, mytype=self.mytype, cpname=self.cpname, fieldname=self.fieldname, name=self.name, dev=self.device, bit=self.bit, suf=self.suffix)

    def __eq__(self, other):
        return self.cpname == other.cpname and self.fieldname == other.fieldname and self.device == other.device and self.bit == other.bit

    def __lt__(self, other):
        return self.cpname == other.cpname and self.fieldname == other.fieldname and (self.device * 16 + self.bit) < (other.device * 16 + other.bit)

class Indications(IOCollection):
    def __init__(self, cpname):
        super(Indications, self).__init__(cpname, None, "Indications", 10)

    def addI(self, name, xml, list=None):
        super(Indications, self).add(Indication(name, xml), list)


class Indication(IOData):
    def __init__(self, cpname, xml):
        n = xml.attrib['name']
        d = xml.attrib['word']
        b = xml.attrib['bit']
        super(Indication, self).__init__(cpname, None, "Indication", n, "K", d, b)

class Controls(IOCollection):
    def __init__(self, cpname):
        super(Controls, self).__init__(cpname, None, "Controls", 10)

    def addC(self, name, xml, list=None):
        super(Controls, self).add(Control(name, xml), list)

class Control(IOData):
    def __init__(self, cpname, xml):
        n = xml.attrib['name']
        d = xml.attrib['word']
        b = xml.attrib['bit']
        super(Control, self).__init__(cpname, None, "Control", n, "S", d, b)

class FieldUnit(IOCollection):
    def __init__(self, cpname, name):
        self.num = 64 + 3   # max number of field unit devices (64 i2c addresses, 3 onboard mcu io-port sets
        self.endat = self.num
        #print('Create Fieldunit: ', cpname, name)
        super(FieldUnit, self).__init__(cpname, name, "FieldUnit", self.num)
        self.bits=16
        self.units = 'Expander'
        self.table      = [[0 for x in range(self.bits+1)] for y in range(self.num+1)]
        self.iomap      = [[0 for x in range(self.bits+1)] for y in range(self.num+1)]
        self.name       = name
        self.expanders  = ExpanderList(self.cpname, name, self)
        self.matrix     = SimpleList(  self.cpname, name, "MatrixList")
        self.lcd        = SimpleList(  self.cpname, name, "LCDList")
        self.signals    = SimpleList(  self.cpname, name, "SignalList")
        self.defines    = {}

    def add(self, child, list = None):
        super(FieldUnit, self).add(child)
        self.iomap[child.device][child.bit] = child.io
        self.table[child.device][child.bit] = '{}_{}'.format(child.io, child.name)
        self.defines[child.name] = '{:02X}{:02X}'.format(child.device, child.bit)

    def tostring(self, indent=0):
        return "{blank:<{indent}}{mytype:<8}: cp: {cpname} {name} children: {num}".format(blank='', indent=indent, mytype=self.mytype, cpname=self.cpname, name=self.name, num=len(self.children))

    def toString(self, indent=0):
        s = self.tostring(indent)
        for k,v in self.children.items():
            cs = ''
            try:
                cs = v.toString(indent+4)
            except AttributeError:
                cs = 'child has no toString() method'
            s = s + '\n' + cs
        return s

    def totext(self):
        self.shrink()
        output = StringIO()
        output.write("  {} {} {} Bits\n".format(self.cpname, self.mytype, self.name))
        for device in range(self.endat):
            output.write("    DDDevice {:<2}: ".format(device))
            for bit in range(self.bits):
                v = self.iomap[device][bit]
                if (isinstance(v, int)):
                    v='-'
                output.write(v)
            output.write("\n")
        contents = output.getvalue()
        output.close()
        contents = contents + '\n' + super(FieldUnit, self).totext()
        return contents

    def UNUSEDtoWiki(self):
        self.shrink()
        output = StringIO()
        output.write("### toWiki")
        output.write("* {} Bits\n".format(self.mytype))
        for device in range(self.endat):
            output.write("** <code>Device {:<2}: ".format(device))
            for bit in range(self.bits):
                v = self.iomap[device][bit]
                if (isinstance(v, int)):
                    v = '-'
                output.write(v)
            output.write("</code>\n")
        contents = output.getvalue()
        output.close()
        return super(FieldUnit, self).towiki() + "\n" + contents

    def sort(self):
        self.shrink()
        d = sorted(self.children.items(), key=lambda v: (v.device * 16 + v.bit))
        self.children = collections.OrderedDict(d)
        self.expanders.sort()
        for k, v in self.children.items():
            try:
                v.sort()
            except AttributeError:
                pass

    def generate(self):
        self.shrink()
        print('calling {}.generate({})'.format(self.mytype, self.name))
        for k, v in self.expanders.children.items():
            print('    child: {} {}'.format(v.mytype, v.name))
            try:
                v.generate()
            except AttributeError:
                pass
        for k, v in self.children.items():
            print('    child: {} {}'.format(v.mytype, v.name))
            try:
                v.generate()
            except AttributeError:
                pass

    def shrink(self):
        if self.endat == self.num:
            for device in range(self.num -1, -1, -1):
                used = False
                for bit in range(self.bits):
                    v = self.iomap[device][bit]
                    if (not isinstance(v, int)):
                        used = True
                if used:
                    self.endat = device
                    break

        if (self.endat + 1) < self.num:
            self.endat = self.endat + 1

class FieldIO(IOData):
    def __init__(self, cpname, fieldname, mytype, name, device, bit, io):
        super(FieldIO, self).__init__(cpname, fieldname, mytype, name, "F", device, bit)
        self.io        = io

class Input(FieldIO):
    def __init__(self, cpname, fieldname, xml):
        n = xml.attrib['name']
        d = xml.attrib['device']
        b = xml.attrib['bit']
        super(Input, self).__init__(cpname, fieldname, "Input", n, d, b, 'I')

class Output(FieldIO):
    def __init__(self, cpname, fieldname, xml):
        n = xml.attrib['name']
        d = xml.attrib['device']
        b = xml.attrib['bit']
        super(Output, self).__init__(cpname, fieldname, "Output", n, d, b, 'O')
        self.type = xml.attrib.get('type')

class SignalMast(SimpleNamedTypedList):
    def __init__(self, cpname, fieldname, xml):
        #SIGFIX: n = 'S{}'.format(xml.attrib['name'])
        n = '{}'.format(xml.attrib['name'])
        super(SignalMast, self).__init__(cpname,  n, "SignalMast")
        self.fieldname = fieldname
        self.doc = xml.attrib.get("doc")

    def toString(self, indent=0):
        s = "{blank:<{indent}}{type:<8}: cp: {cpname} name: {name}".format(blank='', indent=indent, type=self.mytype, cpname=self.cpname, name=self.name)
        for k, v in self.children.items():
            s = s + '\n' + v.toString(indent+4) # Heads...
        return s

class SignalMastHead(SimpleList):
    def __init__(self, cpname, fieldname, xml):
        n = xml.attrib['name']
        super(SignalMastHead, self).__init__(cpname, fieldname, "SignalMastHead")
        self.name = n
        self.field = FieldUnit(cpname, fieldname)
        self.type = xml.attrib.get("type")
        self.bits = xml.attrib.get("bits")
        self.doc = xml.attrib.get("doc")

    def toString(self, indent=0):
        s = "{blank:<{indent}}{mytype:<8}: cp: {cpname} name: {name} type {type} bits {bits}".format(blank='', indent=indent, mytype=self.mytype, cpname=self.cpname, name=self.name, type=self.type, bits=self.bits)
        s = s + '\n' + self.field.toString(indent+4)
        return s

    def towiki(self):
        s = ''
        for k, v in self.children.items():
            cs = ''
            try:
                cs = v.towiki()
            except AttributeError:
                try:
                    cs += v.toString()
                except:
                    cs += 'child has no toString() method'
            s = s + '\n\t' + cs
        return s

    def totext(self):
        s = ''
        for k, v in self.children.items():
            cs = ''
            try:
                cs = v.totext()
            except AttributeError:
                try:
                    cs += v.toString()
                except:
                    cs += 'child has no toString() method'
            s = s + '\n\t' + cs
        return s


class ExpanderList(IOCollection):
    def __init__(self, cpname, fieldname, field):
        #print('Create ExpanderList: ', cpname, fieldname)
        super(ExpanderList, self).__init__(cpname, fieldname, "Expanders", 64)
        self.fieldname = fieldname
        self.field = field
        self.bits=16 # largest possible
        self.table      = [[0 for x in range(self.bits+1)] for y in range(self.num+1)]

    def totext(self):
        heading  = '          {} for {}\t\t   (1=input, 0=output)\n'.format(self.mytype, self.cpname)
        tBegin   = '          +-------------------------------------------------------------------------------+\n'
        tEnd     = tBegin

        devname  = '  Dev {:>2}  | '
        prepend3 = '| I2C Address: {}'
        prepend4 = '           -na-'
        fmt8     = "{type:<16}\t{a:<14}\t|  I/O Map: {init:<16}{pad:9}|\n"
        return self.tableGenerator(heading, tBegin, '', '', '', devname, prepend3, prepend4, '', tEnd, fmt8)

    def towiki(self):
        heading  = '<table border=1 style="font-family: monospace;width: 70%;">\n<tr>\n    <th colspan="4"> {} for {}</th>\n</tr>\n'.format(self.mytype, self.cpname, self.fieldname)
        tBegin   = '<tr>\n<th> Expander\n</th>\n<th> Type\n</th>\n<th> I2C Address\n</th>\n<th> I/O Map\n<br \>bit{} ... (1=input, 0=output) ... bit0\n</th>\n</tr>\n'.format(self.bits - 1)
        devname  = '<tr>\n<th> {:<2} </th>  '
        prepend3 = ' 0x{:02x} '
        prepend4 = ' -na- '
        tEnd     = '</table>\n'
        fmt8     = '<th> {type} </th>\n<td align="center"> {a} </td>\n<td align="center"> {init} </td>'

        return self.tableGenerator(heading, tBegin, '', '', '', devname, prepend3, prepend4, '', tEnd, fmt8)

    def tableGenerator(self, heading, tBegin, prepend, prepend2, postpend, devname, prepend3, prepend4, postpend2, tEnd, fmt8):
        output = StringIO()
        output.write(heading)
        output.write(tBegin)
        count = 0
        for key, val in self.children.items():
            count += 1
            output.write(devname.format(val.device))
            if -1 != val.address():
                a = prepend3.format(int(val.address(), 16))
            else:
                a = prepend4
            output.write(fmt8.format(type=val.type, addr=val.address(), a=a, init=val.initstring, pad='', dev=val.device))
        output.write(tEnd)
        contents = output.getvalue()
        output.close()
        return contents

    def toDetailedWiki(self):
        output = StringIO()
        cpname = self.cpname
        tablename = self.mytype

        def header(output, size):
            output.write('<tr>\n<th>  # </th>\n')
            output.write('    <th>  Device </th>\n\n')
            output.write('    <th>  i2c    </th>\n\n')
            output.write('    <th>  Bit    </th>\n\n')
            output.write('    <th>  Signal </th>\n\n')
            output.write('    <th>  Bit    </th>\n\n')
            output.write('    <th>  Signal </th>\n\n')
            if (int(size) > 8):
                output.write('    <th>  Bit    </th>\n\n')
                output.write('    <th>  Signal </th>\n\n')
                output.write('    <th>  Bit    </th>\n\n')
                output.write('    <th>  Signal </th>\n\n')
            output.write('</tr>\n')

        colspan = 0
        for key, val in self.children.items():
            if val.size is None or val.size == 8:
                c = 7
            else:
                c = 11

            if c > colspan:
                colspan = c

        output.write('<p>{name} Wiring for {cp}\n</p>\n'.format(name=tablename, cp=cpname))
        output.write('<table border=1 style="font-family: monospace; width: 80%;">\n')

        count = 0
        for key, val in self.children.items():
            count += 1
            i2ctype = ' ' + val.type
            i2caddr = val.address()
            if val.size is None or val.size == 8:
                b = 8
            else:
                b = 16
            if i2caddr == -1:
                a='-na-'
            else:
                a='{:<2}'.format(i2caddr)

            header(output, val.size)
            output.write('<tr>\n')
            prefix='\n    <th rowspan=4> {num} </th>\n    <th rowspan=4>  {name} </th>\n    <th rowspan=4> {addr} </th>\n'.format(
                num=val.device,
                name=i2ctype,
                addr=a)
            for bit in range(int(self.bits / 4)):
                output.write(prefix)
                prefix = '<tr>\n'
                for shift in 12,8,4,0: #for shift in 0,4,8,12:
                    shiftedbit = bit + shift
                    if (shiftedbit) < b:
                        v = self.field.table[count - 1][shiftedbit]
                        if (isinstance(v, int)):
                            v = '&nbsp;&nbsp;- - -'
                        if (len(v) > 2) and (v[1] == '_') and ((v[0].upper() == 'I') or (v[0].upper() == 'O')):
                            v = v[:1].lower() + ' ' + v[2:]
                        output.write('\n    <td> {} </td>\n'.format(shiftedbit))
                        output.write('\n    <td> {} </td>\n'.format(v))
                output.write('\n</tr>\n')
        output.write('\n</table>\n')
        contents = output.getvalue()
        output.close()
        return contents


    def toDetailedText(self):
        output = StringIO()
        cpname = self.cpname
        tablename = self.mytype
        header16 = '          +----------------------+------+----------+------+----------+------+----------+------+----------+'
        title16  = '          | Dev         I2C addr |  Bit |  Signal  |  Bit |  Signal  |  Bit |  Signal  |  Bit |  Signal  |'
        header8  = '          +----------------------+------+----------+------+----------+'
        title8   = '          | Dev         I2C addr |  Bit |  Signal  |  Bit |  Signal  |'
        

        output.write('          {} for {}\n'.format(tablename, cpname))

        count = 0
        for key, val in self.children.items():
            count += 1
            i2ctype = ' ' + val.type
            i2caddr = val.address()
            
            if val.size is None or val.size == 8:
                h=header8
                t=title8
                b=8
            else:
                h=header16
                t=title16
                b=16
            
            output.write('{h}\n{t}\n{h}\n'.format(h=h, t=t))
            
            prefix='          |{:>2} {:<13} '.format(val.device, i2ctype)
            for bit in range(int(self.bits / 4)):
                output.write(prefix)
                prefix = '          |{:>2} {:<13}   '.format('', '')
                for shift in 0,4,8,12:
                    if (bit + shift) < b:
                        v = self.field.table[count - 1][bit + shift]
                        if (isinstance(v, int)):
                            v = '- - -'
                        if (len(v) > 2) and (v[1] == '_') and ((v[0] == 'I') or (v[0] == 'O')):
                            v = v[:1].lower() + ' ' + v[2:]
                        if bit + shift == 0:
                            if (i2caddr != -1):
                                output.write('{:<2} |'.format(i2caddr))
                            else:
                                output.write('{:<2} |'.format("na"))
                        elif shift == 0:
                            output.write('   |')
                        output.write('   {:<2} | '.format(str(bit + shift)))
                        output.write('{:<9}|'.format(v))
                output.write('\n')
                i2ctype = ''
                i2caddr = -1
        output.write('{h}\n'.format(h=h, t=t))
        contents = output.getvalue()
        output.close()
        return contents

    def sort(self):
        self.children = dict(sorted(self.children.items(), key=lambda item: item[1]))

    # generate init strings for the expanders based on the field's I's and O's
    def generate(self):
        for device in range(self.num):
            devaddr = str(device)
            if devaddr not in self.children:
                continue
            size  = self.bits  # TODO: need to get expander size (number of bits) from exp device entry...
            typedvalue = ''
            binvalue = ''
            s=''
            for bit in range(size, 0, -1):
                v = self.field.iomap[device][bit-1]
                if isinstance(v, int):
                    v='0'
                elif v == 'I':
                    v = '1'
                elif v == 'O':
                    v = '0'
                else:
                    v='?'
                s=s+v

                if (bit == 13) or (bit == 9) or (bit == 5) or (bit == 1):
                    sep=', '
                    v = ''
                    if (s == '0111'):
                        v = "FieldIO::TURTLE"
                        sep = ',  '
                    elif (s == '0000'):
                        v = "FieldIO::OUTPUTS"
                    elif (s == '1111'):
                        v = "FieldIO::INPUTS "
                    else:
                        v = "FieldIO:PT_" + s
                    if bit > 1:
                        v = v + sep
                    typedvalue = typedvalue + v
                    binvalue = binvalue + s
                    s = ''

            dev = self.children[devaddr]
            initstring = binvalue
            if initstring == '':
                if size == 4:
                    initstring = '0000'
                elif size == 6:
                    initstring = '000000'
                elif size == 8:
                    initstring = '00000000'
                elif size == 16:
                    initstring = '0000000000000000'
            dev.initstring = initstring
            dev.typedinit  = typedvalue

class Expander(IOData):
    def __init__(self, cpname, fieldname, xml):
        d = xml.attrib['device']
        a = xml.attrib['address']
        t = xml.attrib['type']
        s = xml.attrib.get("size")
        n = '{}'.format(d)
        if s is None:
            s = '8'

        super(Expander, self).__init__(cpname, fieldname, "Expander", n, "_E", d, s)
        self.initstring=''
        self.type = t
        self.size = s
        self.addr = a

    def address(self):           return self.addr

    def toString(self):
        return "{}: type: {:<12} init: {:<8} size: {:<8}".format(super(Expander, self).toString(), self.type, self.initstring, self.size)


#############################################################################
# Appliances
#############################################################################

class ApplianceList(SimpleList):
    def __init__(self, cpname):
        super(ApplianceList, self).__init__(cpname, None, "ApplianceList")
        self.tc = {}                # Track Circuits
        self.sections = {}          # Collections of TCs
        self.sw = {}                # Switches
        self.mc = {}                # Maintainer Call
        self.trackpower = {}        # DCC Circuit breakers etc
        self.sig = {}               # Signals
        self.mast = {}              # Heads

    def toString(self):
        s = "{:<8}: cp: {} name: {}".format(
            self.mytype, self.cpname, self.name)
        for k,v in self.children.items():
            s = s + '\n\t\tchildren:   ' + v.toString()
        for k,v in self.tc.items():
            s = s + '\n\t\ttc:         ' + v.toString()
        for k,v in self.sections.items():
            s = s + '\n\t\tsection:    ' + v.toString()
        for k,v in self.sw.items():
            s = s + '\n\t\tsw:         ' + v.toString()
        for k,v in self.mc.items():
            s = s + '\n\t\tmc:         ' + v.toString()
        for k, v in self.trackpower.items():
            s = s + '\n\t\ttrackpower: ' + v.toString()
        for k,v in self.sig.items():
            s = s + '\n\t\tsig:        ' + v.toString()
        for k,v in self.mast.items():
            s = s + '\n\t\tmast:       ' + v.toString()
        return s + '\n'

class Appliance(object):
    def __init__(self, cpname, xml):
        self.cpname = cpname
        self.mytype = "Appliance"
        self.name   = xml.attrib['name']
        if ':' not in self.name:
            self.fullname = '{}_{}'.format(cpname, self.name)
        else:
            self.fullname = self.name.replace(':', '_')
        self.ls = '{cp}_{name}{flag}'
        self.doc = xml.attrib.get("doc")

    def toString(self):
        return "{:<8}: cp: {} name: {} doc: {}".format(
            self.mytype, self.cpname, self.name, self.doc)

    def toSignalCode(self, extended=True):
        return '/* ERROR: {}{} has no impact on routes */'.format(self.mytype, self.name)

    def nodeName(self):
        return 'NODE_{}'.format(self.cpname.upper())

    def prefix(self, flag):
        return self.ls.format(cp=self.cpname, name=self.name, flag=flag)

    def Name(self, ind=False, ctl=False):
        if ind:
            flag = 'K'
        elif ctl:
            flag = 'S'
        else:
            flag = 'F'
        return self.prefix(flag)

class SIG_Appliance(SimpleList):
    def __init__(self, cpname, xml):
        super(SIG_Appliance, self).__init__(cpname, None, "SIG_Appliance")
        self.name       = xml.attrib['name']
        self.er         = xml.attrib.get('ER')
        self.fleet      = xml.attrib.get('FLEET')
        self.knockdown  = SimpleList(self.cpname, None, 'SIG_Knockdowns')
        self.mast       = SimpleList(self.cpname, None, 'SIG_Heads')
        self.fullname   = "{}_SIG{}".format(self.cpname, self.name)
        self.iTE        = "{}_{}TEK".format(self.cpname, self.name)
        self.iNorth     = "{}_{}NGK".format(self.cpname, self.name)
        self.iSouth     = "{}_{}SGK".format(self.cpname, self.name)
        self.cNorth     = "{}_{}NGS".format(self.cpname, self.name)
        self.cSouth     = "{}_{}SGS".format(self.cpname, self.name)
        self.cStop      = "{}_{}HS" .format(self.cpname, self.name)
        self.doc = xml.attrib.get("doc")
        # print('----{} {}----\nDoc: {}\n'.format(self.mytype, self.name, self.doc))

    def iLeft(self):
        return self.iNorth

    def iRight(self):
        return self.iSouth

    def iTimer(self):
        return self.iTE

    def cLeft(self):
        return self.cNorth

    def cRight(self):
        return self.cSouth

    def cSTOP(self):
        return self.cStop

    # North, South, STOP
    # heads
    def getMast(self, name):
        for mastname, mast in self.mast.children.items():
            fullname = '{}:{}'.format(mast.cpname, mastname)
            if fullname == name:
                return mast
        return None

    def toString(self):
        s = "{:<8}: cp: {} name: {} (er: {} fleet: {})".format(
            self.mytype, self.cpname, self.name, self.er, self.fleet)
        for k, v in self.knockdown.children.items():
            s = s + '\n\t\tKnockdown: ' + v.toString()
        for k,v in self.mast.children.items():
            s = s + '\n\t\tHead:      ' + v.toString()
        for k,v in self.children.items():
            s = s + '\n\t\tchildren:  ' + v.toString()
        return s

class MAST_Appliance(SimpleList):
    def __init__(self, cpname, xml):
        super(MAST_Appliance, self).__init__(cpname, None, "MAST_Appliance")
        self.name      = xml.attrib['name']
        self.direction = xml.attrib['direction']
        self.bits      = xml.attrib.get('bits')
        self.route     = Route(self.cpname, xml)
        self.doc = xml.attrib.get("doc")
        #print('----{} {}----\nDoc: {}\n'.format(self.mytype, self.name, self.doc))

    def toString(self):
        s = "{:<8}: cp: {} name: {} direction: {} bits: {}".format(
            self.mytype, self.cpname, self.name, self.direction, self.bits)
        for k,v in self.route.children.items():
            s = s + '\n\t\t\t' + v.toString()
        return s

class Route(SimpleNamedTypedList):
    def __init__(self, cpname, xml):
        super(Route, self).__init__(cpname, xml.attrib['name'],  "Route")
        self.default_aspect = xml.attrib.get('aspect')
        self.doc = xml.attrib.get("doc")
        #print('----{} {}----\nDoc: {}\n'.format(self.mytype, self.name, self.doc))

    def toString(self):
        s = "{:<8}: cp: {} name: {}".format(self.mytype, self.cpname, self.name)
        for k, v in self.children.items():
            s = s + '\n\t\t\t\t' + v.toString()
        return s

class SW_Appliance(Appliance):
    def __init__(self, cpname, xml):
        super(SW_Appliance, self).__init__(cpname, xml)
        self.mytype = "SW_Appliance"
        if ':' not in self.name:
            self.fullname = '{}_SW{}'.format(cpname, self.name)
        self.normal    = xml.attrib.get('normal')
        self.reverse   = xml.attrib.get('reverse')
        self.motor     = xml.attrib.get('motor')
        self.trackcircuit = xml.attrib.get('trackcircuit')
        if self.trackcircuit is None:
            self.trackcircuit = '{}T1'.format(self.name)
        self.tc        = '{}:{}'.format(cpname, xml.attrib.get('trackcircuit'))
        self.slave     = xml.attrib.get('slaveto')
        self.invert    = xml.attrib.get('invert')
        self.source    = xml.attrib.get('source')
        self.indication  = xml.attrib.get('indication')
        self.Ns = '{cp}_{name}NW{flag}'
        self.Rs = '{cp}_{name}RW{flag}'
        if self.indication is None:
            if self.normal  is None: self.normal  =       self.name + 'NW'
            if self.reverse is None: self.reverse =       self.name + 'RW'
            if self.motor   is None: self.motor   = 'T' + self.name

    #     if (DOM.hasAttribute("indication")):
    #         f["indication"] = DOM.getAttribute("indication")
    #     f["normal"]          =  ""   + id  + "NW"
    #     f["reverse"]         =  ""   + id  + "RW"
    #     f["motor"]           =  "T"  + id
    #     f["normalname"]      =  "F"  + id  + "NW"
    #     f["reversename"]     =  "F"  + id  + "RW"
    #     f["motorname"]       =  "FT" + id
    #     f["normallongname"]  =  controlpoint + "_F"  + id  + "NW"
    #     f["reverselongname"] =  controlpoint + "_F"  + id  + "RW"
    #     f["motorlongname"]   =  controlpoint + "_FT" + id
    #     me["field"] = f
    #     dict[id] = me

    def toString(self):
        return "{:<8}: cp: {} name: {} full: {} N: {} R: {} M: {} tc: {} slave: {} invert: {} source: {} indication: {}".format(
            self.mytype, self.cpname, self.name, self.fullname, self.iN(), self.iR(), self.motor, self.tc, self.slave, self.invert, self.source, self.indication)

    def _name(self, s, v, n):
        return s.format(cp=self.cpname, flag=v, name=n)

    def TC(self):
        if ':' in self.name:
            return self.tc
        return '{}_{}'.format(self.cpname, self.tc)

    def fM(self):
        if self.motor is None:
            return '-1'
        return '{cpname}_{name}{flag}'.format(cpname=self.cpname, name=self.motor, flag='F')

    def _NR(self, n, r, ind=False, ctl=False, slav=False):
        s = n
        nam = self.name

        if slav:
            if self.invert is not None and (self.invert.lower() == "true" or self.invert.lower() == "1"):
                s = r
            if self.slave is not None:
                nam = self.slave
        if ind:
            flag = 'K'
        elif ctl:
            flag = 'S'
        else:
            flag = 'F'
        return self._name(s, flag, nam)

    def _N(self, ind = False, ctl = False, slav=False):
        if ':' in self.name:
            return self.normal
        return self._NR(self.Ns, self.Rs, ind, ctl, slav)

    def _R(self, ind = False, ctl = False, slav=False):
        if ':' in self.name:
            return self.reverse
        return self._NR(self.Rs, self.Ns, ind, ctl, slav)
    # field
    def fN(self):
        return self._N(False, False, False)

    def fR(self):
        return self._R(False, False, False)
    # indications
    def iN(self):
        return self._N(True, False, False)

    def iR(self):
        return self._R(True, False, False)
    # controls
    def cN(self):
        return self._N(False, True, False)

    def cR(self):
        return self._R(False, True, False)
    # slave devices follow their masters
    def sN(self):
        return self._N(False, True, True)

    def sR(self):
        return self._R(False, True, True)

class SW_Route(Appliance):
    def __init__(self, cpname, xml):
        super(SW_Route, self).__init__(cpname, xml)
        if ':' not in self.name:
            self.fullname = '{}_SW{}'.format(cpname, self.name)
        self.mytype = "SW_Route"
        self.position = xml.attrib['position']
        self.aspect   = xml.attrib.get('aspect')

    def toString(self):
        return "{:<8}: cp: {} name: {} pos: {} asp: {}".format(
            self.mytype, self.cpname, self.name, self.position, self.aspect)

    def toAspect(self):
        if self.aspect == 'CLEAR':
            asp = 'CLEAR'
        elif self.aspect == 'APPROACH_DIVERGING':
            asp = self.aspect
        elif self.aspect == 'ADVANCE_APPROACH':
            asp = self.aspect
        elif self.aspect == 'APPROACH_LIMITED':
            asp = self.aspect
        elif self.aspect == 'LIMITED_CLEAR':
            asp = self.aspect
        elif self.aspect == 'APPROACH_MEDIUM':
            asp = self.aspect
        elif self.aspect == 'APPROACH_RESTRICTING':
            asp = self.aspect
        elif self.aspect == 'APPROACH_SLOW':
            asp = self.aspect
        elif self.aspect == 'APPROACH':
            asp = self.aspect
        elif self.aspect == 'MEDIUM_CLEAR':
            asp = self.aspect
        elif self.aspect == 'DIVERGING_CLEAR':
            asp = self.aspect
        elif self.aspect == 'SLOW_CLEAR':
            asp = self.aspect
        elif self.aspect == 'LIMITED_APPROACH':
            asp = self.aspect
        elif self.aspect == 'MEDIUM_APPROACH':
            asp = self.aspect
        elif self.aspect == 'DIVERGING_ADVANCE_APPROACH':
            asp = self.aspect
        elif self.aspect == 'DIVERGING_APPROACH_DIVERGING':
            asp = self.aspect
        elif self.aspect == 'DIVERGING_RESTRICTING':
            asp = self.aspect
        elif self.aspect == 'SLOW_APPROACH':
            asp = self.aspect
        elif self.aspect == 'RESTRICTING':
            asp = self.aspect
        elif self.aspect == 'STOP':
            asp = self.aspect
        elif self.aspect == 'DARK':
            asp = self.aspect
        else:
            asp = 'ASPECT_UNKNOWN'
        return 'Aspects::' + asp

    def toPosition(self, short=False):
        pos = 'UNKNOWN'
        if self.position == 'R':
            pos = 'REVERSE'
        elif self.position == 'N':
            pos = 'NORMAL'
        if not short:
            pos = "SwitchDevice::" + pos
        return pos

    def toHTML(self, extended=True):
        pos = self.toPosition(short=True)
        asp = self.toAspect()

        Item="{cpname}:{name}".format(cpname=self.cpname, name=self.name)
        Value='{asp},'.format(asp=asp)
        if extended:
            Condition = '{pos},'.format(pos=pos)
            r= '{Item:<25} {Condition:<35} {Value:<35} Aspects::STOP'.format(Item=Item, Condition=Condition, Value=Value)
        else:
            Condition = '{pos}'.format(pos=pos)
            r= '{Item:<25} {Condition}'.format(Item=Item, Condition=Condition, Value=Value)
        return r.replace(' ', '&nbsp;')

    '''
    Called by MAKO template
    '''
    def toSignalCode(self, extended=True):
        pos = self.toPosition()
        asp = self.toAspect()

        #TFIX: Item="{cpname}:T{name}".format(cpname=self.cpname, name=self.name)
        Item="{cpname}:{name}".format(cpname=self.cpname, name=self.name)
        Func='fieldUnit->get("{Item}"),'.format(Item=Item)
        Value='{asp},'.format(asp=asp)
        if extended:
            Condition = '{pos},'.format(pos=pos)
            return '{Func:<45} {Condition:<35} {Value:<35} Aspects::STOP'.format(Func=Func, Condition=Condition, Value=Value)
        else:
            Condition = '{pos}'.format(pos=pos)
            return '{Func:<45} {Condition}'.format(Func=Func, Condition=Condition, Value=Value)

class IND_Route(Appliance):
    def __init__(self, cpname, xml):
        super(IND_Route, self).__init__(cpname, xml)
        if ':' not in self.name:
            print("ERROR: route type 'indication' can only refer to a fully qualified control point value\n")
        self.fullname = self.name.replace(':', '_')
        self.othercpname = self.name.split(":", 1)[0]
        self.aspect   = xml.attrib.get('aspect')
        self.invert   = xml.attrib.get('invert')
        self.mytype = "IND_Route"

    def toString(self):
        return "{:<8}: cp: {} name: {} fullname: {} othercpnamne {} aspect: {}".format(
            self.mytype, self.cpname, self.name, self.fullname, self.othercpname, self.aspect)


class SIG_Route(Appliance):
    def __init__(self, cpname, xml):
        super(SIG_Route, self).__init__(cpname, xml)
        if ':' not in self.name:
            self.fullname = '{}_SIG{}'.format(cpname, self.name)
        self.mytype    = "SIG_Route"
        self.direction = xml.attrib['direction']
        self.aspect    = xml.attrib.get('aspect')
        self.sig       = None    # parent signal (set by parser...)

    def toString(self):
        return "{:<8}: cp: {} name: {} pos: {} asp: {}".format(
            self.mytype, self.cpname, self.name, self.direction, self.aspect)

    def toHTML(self, extended=True):
        pos = 'UNKNOWN'
        if self.direction == 'LEFT':
            pos = 'LEFT'
        elif self.direction == 'RIGHT':
            pos = 'RIGHT '

        if self.aspect is None:
            asp = "Aspects::CLEAR"
        else:
            asp = "Aspects::" + self.aspect

        Item="{cpname}:{name}".format(cpname=self.cpname, name=self.name)
        Value='{asp},'.format(asp=asp)
        if extended:
            Condition = '{pos},'.format(pos=pos)
            r= '{Item:<25} {Condition:<35} {Value:<35} Aspects::STOP'.format(Item=Item, Condition=Condition, Value=Value)
        else:
            Condition = '{pos}'.format(pos=pos)
            r= '{Item:<25} {Condition}'.format(Item=Item, Condition=Condition, Value=Value)
        return r.replace(' ', '&nbsp;')

    '''
    Called by MAKO template
    '''
    def toSignalCode(self, extended=True):
        pos = 'SignalDevice::UNKNOWN'
        if self.direction == 'LEFT':
            pos = 'SignalDevice::LEFT'
        elif self.direction == 'RIGHT':
            pos = 'SignalDevice::RIGHT '

        if self.aspect is None:
            asp = "Aspects::CLEAR"
        else:
            asp = "Aspects::" + self.aspect

        #SIGFIX: Item="{cpname}:S{name}".format(cpname=self.cpname, name=self.name)
        Item="{cpname}:{name}".format(cpname=self.cpname, name=self.name)
        Func='fieldUnit->get("{Item}"),'.format(Item=Item)
        Value='{asp},'.format(asp=asp)
        if extended:
            Condition='{pos},'.format(pos=pos)
            return '{Func:<45} {Condition:<35} {Value:<35} Aspects::STOP'.format(Func=Func, Condition=Condition, Value=Value)
        else:
            Condition='{pos}'.format(pos=pos)
            return '{Func:<45} {Condition}'.format(Func=Func, Condition=Condition, Value=Value)

class TC_Appliance(Appliance):
    def __init__(self, cpname, xml):
        super(TC_Appliance, self).__init__(cpname, xml)
        self.mytype    = "TC_Appliance"
        self.fTC       = xml.attrib.get('indication')
        self.ls        = '{cp}_{name}{flag}'
        self.slave     = xml.attrib.get('slaveto')
        self.type      = xml.attrib.get('type') # reverse?

    def toString(self):
        return "{:<8}: cp: {} name: {} slave: {}".format(
            self.mytype, self.cpname, self.name, self.slave)

    def toHTML(self, extended=True):
        Item="{cpname}:{name}".format(cpname=self.cpname, name=self.name)
        Value='{asp},'.format(asp='Aspects::CLEAR')
        if extended:
            Condition = '{pos},'.format(pos='TrackCircuitDevice::UNOCCUPIED')
            Condition = '{pos},'.format(pos='UNOCCUPIED')
            r= '{Item:<25} {Condition:<35} {Value:<35} Aspects::STOP'.format(Item=Item, Condition=Condition, Value=Value)
        else:
            Condition = '{pos}'.format(pos='TrackCircuitDevice::UNOCCUPIED')
            Condition = '{pos}'.format(pos='UNOCCUPIED')
            r= '{Item:<25} {Condition}'.format(Item=Item, Condition=Condition, Value=Value)
        return r.replace(' ', '&nbsp;')

    '''
    Called by MAKO template
    '''
    def toSignalCode(self, extended=True):
        Item="{cpname}:{name}".format(cpname=self.cpname, name=self.name)
        Func='fieldUnit->get("{Item}"),'.format(Item=Item)
        Value='{asp},'.format(asp='Aspects::CLEAR')
        if extended:
            Condition = '{pos},'.format(pos='TrackCircuitDevice::UNOCCUPIED')
            return'{Func:<45} {Condition:<35} {Value:<35} Aspects::STOP'.format(Func=Func, Condition=Condition, Value=Value)
        else:
            Condition = '{pos}'.format(pos='TrackCircuitDevice::UNOCCUPIED')
            return'{Func:<45} {Condition}'.format(Func=Func, Condition=Condition, Value=Value)

class Section_Appliance(Appliance):
    def __init__(self, cpname, xml):
        super(Section_Appliance, self).__init__(cpname, xml)
        self.mytype    = "Section_Appliance"
        self.TCs       = {}

    def toString(self):
        s = "{:<8}: cp: {} name: {}".format(self.mytype, self.cpname, self.name)
        for k, v in self.TCs.items():
            s = s + '\n\t\ttc:  ' + v.toString()
        return s

    def toHTML(self, extended=True):
        Item="{cpname}:{name}".format(cpname=self.cpname, name=self.name)
        Value='{asp},'.format(asp='Aspects::CLEAR')
        if extended:
            Condition = '{pos},'.format(pos='TrackCircuitDevice::UNOCCUPIED')
            Condition = '{pos},'.format(pos='UNOCCUPIED')
            r= '{Item:<25} {Condition:<35} {Value:<35} Aspects::STOP'.format(Item=Item, Condition=Condition, Value=Value)
        else:
            Condition = '{pos}'.format(pos='TrackCircuitDevice::UNOCCUPIED')
            Condition = '{pos}'.format(pos='UNOCCUPIED')
            r= '{Item:<25} {Condition}'.format(Item=Item, Condition=Condition, Value=Value)
        return r.replace(' ', '&nbsp;')

    '''
    Called by MAKO template
    '''
    def toSignalCode(self, extended=True):
        Item="{cpname}:{name}".format(cpname=self.cpname, name=self.name)
        Func='fieldUnit->get("{Item}"),'.format(Item=Item)
        Value='{asp},'.format(asp='Aspects::CLEAR')
        if extended:
            Condition = '{pos},'.format(pos='TrackCircuitDevice::UNOCCUPIED')
            return'{Func:<45} {Condition:<35} {Value:<35} Aspects::STOP'.format(Func=Func, Condition=Condition, Value=Value)
        else:
            Condition = '{pos}'.format(pos='TrackCircuitDevice::UNOCCUPIED')
            return'{Func:<45} {Condition}'.format(Func=Func, Condition=Condition, Value=Value)

class MC_Appliance(Appliance):
    def __init__(self, cpname, xml):
        super(MC_Appliance, self).__init__(cpname, xml)
        self.mytype = "MC_Appliance"

    def toString(self):
        return "{:<8}: cp: {} name: {}".format(
            self.mytype, self.cpname, self.name)


class TrackPower_Appliance(Appliance):
    def __init__(self, cpname, xml):
        super(TrackPower_Appliance, self).__init__(cpname, xml)
        self.mytype = "TrackPower_Appliance"

    def toString(self):
        return "{:<8}: cp: {} name: {}".format(
            self.mytype, self.cpname, self.name)

##
# CTC appliances
##

class CTC_Appliance(Appliance):
    def __init__(self, cpname, mytype, xml):
        super(CTC_Appliance, self).__init__(cpname, xml)

        self.mytype = mytype
        if self.name.startswith(':'):
            self.name = cpname + self.name
            self.cpname = cpname
        else:
            self.cpname = re.sub(r"(.*):.*$", r"\1", self.name)
        # self.name     = self.name + "K"
        self.name     = self.name.replace(":", "_")
        self.position = xml.attrib.get("position")
        self.color    = xml.attrib.get("color")
        self.label    = xml.attrib.get("label")
        #self.slave    = xml.attrib.get("slaveto")





'''
    All the above classes and methods are used by the ControlPoint class to build an in-memory
    model of the, ahem, control point.

    The ControlPoint class instance is passed to a MAKO template for expansion into code instances,
    for example, Arduino sketches, python debugging and testing routines, wiki documentation, etc
'''
class ControlPoint:
    """
    Wrap the components of a control point
    """
    def gotDependency(self, cpname):
        # if the dependency is on me, True
        if self.name == cpname:
            return True
        # if my parent can resolve the dependency, True
        if self.parent is not None and self.parent.gotDependency(cpname):
            return True
        # otherwise, have I already ingested this as a child dependency?
        return cpname in self.depends

    def getSig(self, name):
        for signame, sig in self.appliances.sig.items():
            #SIGFIX: sigfullname = '{}:S{}'.format(sig.cpname, signame)
            sigfullname = '{}:{}'.format(sig.cpname, signame)
            if sigfullname == name:
                return sig
        return None


    def gatherDocumentation(self):
        doc = []
        for b in self.root.iterfind("doc"):
            doc.append(b.text)
        return doc

    def gatherControls(self):
        '''
          <controls>
               <switch       name="901"   word="0" bit="0" bits="2"/>
               <switch       name="903"   word="0" bit="2" bits="2"/>
               <switch       name="905"   word="0" bit="4" bits="2"/>
               <switch       name="907"   word="0" bit="6" bits="2"/>

               <switch       name="909"   word="1" bit="0" bits="2"/>
               <signal       name="902"   word="1" bit="2" bits="3" >
               <!-- signals imply 3 bits: South not at stop, North and STOP -->
                  <control   name="902SG" word="1" bit="2" />
                  <control   name="902NG" word="1" bit="3" />
                  <control   name="902H"  word="1" bit="4" />
               </signal>
               <signal       name="904"   word="1" bit="5" bits="3" />

               <unused                    word="2" bit="0" />
               <unused                    word="2" bit="1" />
               <unused                    word="2" bit="2" />
               <unused                    word="2" bit="3" />
               <unused                    word="2" bit="4" />
               <unused                    word="2" bit="5" />
               <unused                    word="2" bit="6" />
               <mcall        name="MC1"   word="2" bit="7" />
          </controls>
        '''

        def addSwitchControl(controls, xml):
            name = xml.attrib.get('name')
            word = xml.attrib.get('word')
            bit = xml.attrib.get('bit')
            nw = etree.Element("xml", name="{}NW".format(name), word=word, bit=str(int(bit) + 0))
            rw = etree.Element("xml", name="{}RW".format(name), word=word, bit=str(int(bit) + 1))
            controls.addC(self.name, nw)
            controls.addC(self.name, rw)

        def addSignalControl(controls, xml):
            name = xml.attrib.get('name')
            word = xml.attrib.get('word')
            bit = xml.attrib.get('bit')
            sg = etree.Element("xml", name="{}SG".format(name), word=word, bit=str(int(bit) + 0))
            ng = etree.Element("xml", name="{}NG".format(name), word=word, bit=str(int(bit) + 1))
            te = etree.Element("xml", name="{}H".format(name),  word=word, bit=str(int(bit) + 2))
            controls.addC(self.name, sg)
            controls.addC(self.name, ng)
            controls.addC(self.name, te)

        def addUnusedControl(controls, xml):
            word = xml.attrib.get('word')
            bit = xml.attrib.get('bit')
            name = 'x{}.{}'.format(word, bit)
            u = etree.Element("xml", name=name, word=word, bit=bit)
            controls.addC(self.name, u)

        def addTrackPowerControl(controls, xml):
            name = xml.attrib.get('name')
            word = xml.attrib.get('word')
            bit = xml.attrib.get('bit')
            on  = etree.Element("xml", name="{}PON". format(name), word=word, bit=str(int(bit) + 0))
            off = etree.Element("xml", name="{}POFF".format(name), word=word, bit=str(int(bit) + 1))
            controls.addC(self.name, on)
            controls.addC(self.name, off)

        controls = Controls(self.name)
        for p in self.root.iterfind("controls"):
            for xml in p.iterfind("switch"):
                addSwitchControl(controls, xml)
            for xml in p.iterfind("lock"):
                addSwitchControl(controls, xml)
            for xml in p.iterfind("trackpower"):
                addTrackPowerControl(controls, xml)
            for xml in p.iterfind("signal"):
                addSignalControl(controls, xml)
            for xml in p.iterfind("unused"):
                addUnusedControl(controls, xml)
            for xml in p.iterfind("trackcircuit"):
                controls.addC(self.name, xml)
            for xml in p.iterfind("mcall"):
                controls.addC(self.name, xml)
            for xml in p.iterfind("control"):
                controls.addC(self.name, xml)
        return controls

    def gatherIndications(self):
        '''
          <indications>
               <switch       name="901"   word="0" bit="0" bits="2"/>
               <switch       name="903"   word="0" bit="2" bits="2"/>
               <switch       name="905"   word="0" bit="4" bits="2"/>
               <switch       name="907"   word="0" bit="6" bits="2"/>

               <switch       name="909"   word="1" bit="0" bits="2" />
               <signal       name="902"   word="1" bit="2" bits="3" />
               <signal       name="904"   word="1" bit="5" bits="3" />

               <trackcircuit name="903T2" word="2" bit="0" />
               <trackcircuit name="905T2" word="2" bit="1" />
               <trackcircuit name="907T2" word="2" bit="2" />
               <trackcircuit name="909T2" word="2" bit="3" />
               <trackcircuit name="1SAT"  word="2" bit="4" />
               <trackcircuit name="2SAT"  word="2" bit="5" />
               <trackcircuit name="3SAT"  word="2" bit="6" />
               <trackcircuit name="4SAT"  word="2" bit="7" />

               <trackcircuit name="1SAAT" word="3" bit="0" />
               <trackcircuit name="2SAAT" word="3" bit="1" />
               <trackcircuit name="3SAAT" word="3" bit="2" />
               <trackcircuit name="4SAAT" word="3" bit="3" />
               <trackcircuit name="901T1" word="3" bit="4" />
               <trackcircuit name="DAT"   word="3" bit="5" />
               <trackcircuit name="YLAD"  word="3" bit="6" />
               <trackcircuit name="LOOP"  word="3" bit="7" />

               <unused                    word="4" bit="0" />
               <unused                    word="4" bit="1" />
               <unused                    word="4" bit="2" />
               <unused                    word="4" bit="3" />
               <unused                    word="4" bit="4" />
               <unused                    word="4" bit="5" />
               <unused                    word="4" bit="6" />
               <mcall        name="MC1"   word="4" bit="7" />
          </indications>
        '''

        def addUnusedIndication(indications, xml):
            word = xml.attrib.get('word')
            bit = xml.attrib.get('bit')
            name = 'x{}.{}'.format(word, bit)
            u = etree.Element("xml", name=name, word=word, bit=bit)
            indications.addI(self.name, u)

        def addSwitchIndication(indications, xml):
            name = xml.attrib.get('name')
            word = xml.attrib.get('word')
            bit = xml.attrib.get('bit')
            nw = etree.Element("xml", name="{}NW".format(name), word=word, bit=str(int(bit) + 0))
            rw = etree.Element("xml", name="{}RW".format(name), word=word, bit=str(int(bit) + 1))
            indications.addI(self.name, nw)
            indications.addI(self.name, rw)

        def addSignalIndication(indications, xml):
            name = xml.attrib.get('name')
            word = xml.attrib.get('word')
            bit = xml.attrib.get('bit')
            sg = etree.Element("xml", name="{}SG".format(name), word=word, bit=str(int(bit) + 0))
            ng = etree.Element("xml", name="{}NG".format(name), word=word, bit=str(int(bit) + 1))
            te = etree.Element("xml", name="{}TE".format(name), word=word, bit=str(int(bit) + 2))
            indications.addI(self.name, sg)
            indications.addI(self.name, ng)
            indications.addI(self.name, te)

        def addTrackPowerIndication(indications, xml):
            name = xml.attrib.get('name')
            word = xml.attrib.get('word')
            bit = xml.attrib.get('bit')
            short = etree.Element("xml", name="{}SHORT".format(name), word=word, bit=str(int(bit) + 0))
            ton   = etree.Element("xml", name="{}TON".  format(name), word=word, bit=str(int(bit) + 1))
            occ   = etree.Element("xml", name="{}OCC".  format(name), word=word, bit=str(int(bit) + 2))
            t     = etree.Element("xml", name="{}OFF".  format(name), word=word, bit=str(int(bit) + 3))
            indications.addI(self.name, short)
            indications.addI(self.name, ton)
            indications.addI(self.name, occ)
            indications.addI(self.name, t)

        indications = Indications(self.name)
        for p in self.root.iterfind("indications"):
            for xml in p.iterfind("switch"):
                addSwitchIndication(indications, xml)
            for xml in p.iterfind("lock"):
                addSwitchIndication(indications, xml)
            for xml in p.iterfind("trackpower"):
                addTrackPowerIndication(indications, xml)
            for xml in p.iterfind("signal"):
                addSignalIndication(indications, xml)
            for xml in p.iterfind("unused"):
                addUnusedIndication(indications, xml)
            for xml in p.iterfind("trackcircuit"):
                indications.addI(self.name, xml)
            for xml in p.iterfind("mcall"):
                indications.addI(self.name, xml)
            for xml in p.iterfind("indication"):
                indications.addI(self.name, xml)
        return indications


    def __init__(self, directory, controlpointfile, parent):
        self.xml     = etree.parse(directory + '/' + controlpointfile)
        self.root    = self.xml.getroot()

        self.parent  = parent
        self.name    = self.root.attrib['name']
        self.node    = self.root.attrib['node']
        self.layout  = self.root.attrib['layout']
        self.FQBN    = self.root.attrib.get('FQBN')
        self.board   = self.root.attrib.get('board')  # obsolete
        self.depends = []
        self.documentation = []
        self.ctcpanel = None

        err = None

        for b in self.root.iterfind("depends"):
            n = b.attrib['name']     # cp name
            f = b.attrib['xmlfile']  # filename for xml
            if not self.gotDependency(n):
                if os.path.isfile(directory + '/' + f):
                    dcp = ControlPoint(directory, f, self)
                    self.depends.append(dcp)    # create a dict of dependent CPs
                else:
                    print("ERROR: Can not resolve dependency: file not found: \"{}\"".format(f))
                    err = True
            else:
                print("Note: CP ", n, " already known")

        if err :
            print("Stopping because of dependency errors")
            return


        self.documentation        = self.gatherDocumentation()
        self.indications          = self.gatherIndications()
        self.controls             = self.gatherControls()

        if self.parent is not None:
            # Dependencies (with a CP as parent) only need indications and controls...
            return

        # Appliances (like indications and controls) are not specific to a particular field unit
        # i.e., there might be a control panel associated with the CP as well...)
        self.appliances = ApplianceList(self.name)

        '''
        <switches>
            <switch name="901"  trackcircuit="901T1" /> <!-- Departure track / reverse loop -->
            <switch name="903"  trackcircuit="YLAD"  /> <!-- Yard Track 1 -->
            <switch name="905"  trackcircuit="YLAD"  /> <!-- Yard Track 2 -->
            <switch name="907"  trackcircuit="YLAD"  /> <!-- Yard Track 3 -->
            <switch name="909"  trackcircuit="YLAD"  /> <!-- Yard Track 4 -->
        </switches>
        
        Attributes Required:
            'name'          # <odd ordinal number>
        Attributes Optional
            'normal'        # <name>NW
            'reverse'       # <name>RW
            'motor'         # T<name>
            'trackcircuit'  # <name>T1  - Associated TC used for point locking
            'slaveto'       # None      - Another switch (for a crossover or derail...)
            'invert'        # None      - swap Normal and Reverse motor polarity
            'indication'    # None      - "OtherCP:T1" Remote feedback from another CP's indication packet, no motor control
        '''
        for p in self.root.iterfind("switches"):
            for c in p.iterfind('switch'):
                self.appliances.add(SW_Appliance(self.name, c), self.appliances.sw)

        '''
        <trackcircuits>
            <!-- Turtle -->
            <trackcircuit name="901T1" />

            <!-- T1 - from Turtle,            T2 - IR Detector on points        T3 - IR Detector on Yard Lead -->
            <trackcircuit name="903T1" />     <trackcircuit name="903T2" />     <trackcircuit name="903T3" />
            <trackcircuit name="905T1" />     <trackcircuit name="905T2" />     <trackcircuit name="905T3" />
            <trackcircuit name="907T1" />     <trackcircuit name="907T2" />     <trackcircuit name="907T3" />
            <trackcircuit name="909T1" />     <trackcircuit name="909T2" />     <trackcircuit name="909T3" />

            <!-- IR Detectors for train spotting before end of block -->
            <trackcircuit name="1SAAT" />
            <trackcircuit name="2SAAT" />
            <trackcircuit name="3SAAT" />
            <trackcircuit name="4SAAT" />

            <!-- cpOD block detectors -->
            <trackcircuit name="DAT" />
            <trackcircuit name="1SAT" />
            <trackcircuit name="2SAT" />
            <trackcircuit name="3SAT" />
            <trackcircuit name="4SAT" />
            <trackcircuit name="LOOP" type="reverse"/>
        </trackcircuits>

        Attributes Required:
            'name'          # <alphanum>T<num>
        Attributes Optional:
            'type'          # Default 'noreverse', 'reverse'   # Reverse Loop changes flow of traffic
            'indication'    # "OtherCP:1SAT" Remote feedback from another CP's indication packet
            'slaveto'       # Another TC, as an alias

        '''

        for p in self.root.iterfind("trackcircuits"):
            for c in p.iterfind('trackcircuit'):
                self.appliances.add(TC_Appliance(self.name, c), self.appliances.tc)

        '''
        Arbitrary layout feedback sensors
        <sensors>
            <sensor name="SLIDE" />
        </sensors>
        
        Attributes Required:
            'name'          # <alphanum>
        '''

        for p in self.root.iterfind("sensors"):
            for c in p.iterfind('sensor'):
                self.appliances.add(TC_Appliance(self.name, c), self.appliances.tc)

        '''
        <sections>
            <section name="YLAD" >      <!-- compound collection of the following TCs -->
                <trackcircuit name="903T1" />     <trackcircuit name="903T2" />
                <trackcircuit name="905T1" />     <trackcircuit name="905T2" />
                <trackcircuit name="907T1" />     <trackcircuit name="907T2" />
                <trackcircuit name="909T1" />     <trackcircuit name="909T2" />
            </section>
        </sections>
        
        Attributes Required:
            'name'          # <alphanum>T<num>  # a name for the group of TCs, OCCUPIED whenever ANY of the group is
                list of existing named track curcuits 
        '''

        for p in self.root.iterfind("sections"):
            for section in p.iterfind('section'):
                s = Section_Appliance(self.name, section)
                self.appliances.add(s, self.appliances.sections)
                for circuit in section.iterfind('trackcircuit'): # get list of TCs in this section
                    name=circuit.attrib.get("name")
                    s.TCs[name] = TC_Appliance(self.name, circuit)
        '''
        Do something like light a lamp at the control point, state is shown in indication packets
        
        <actuators>
                <call         name="MC1" />
                <actuator     name="GATE1" />
        </actuators>
        
        Attributes Required:
            'name'          # MC<num> for maintainer calls -or-
            'name'          # <alphanum> for arbitrary actuators

        '''

        for a in self.root.iterfind("actuators"):
            for xml in a.iterfind('call'):
                self.appliances.add(MC_Appliance(self.name, xml), self.appliances.mc)

            for xml in a.iterfind('actuator'):
                self.appliances.add(MC_Appliance(self.name, xml), self.appliances.mc)

            for xml in a.iterfind('trackpower'):
                self.appliances.add(TrackPower_Appliance(self.name, xml), self.appliances.trackpower)


        '''
        In an Interlocking/Control Point...
            Every Signal has one or more Masts associated with it
            A Mast is typically located at one of the three entrances to a switch - points, normal or diverging)
            A Mast governs all the routes that are reachable from it
        
        A Route starts with the sequence of switches that must be passed through when traversing 
        the control point/interlocking.  Notationally, a switch is either normal or (reversed).
        Example:  In an interlocking with 3 facing point turnouts like:
        
                    S2NABC |-O-O
              IN>    ====== ==1==== ==3==== ==5=== =====  R1
                               \\     \\      \\
                                 \\     \\      \\
                                  R2     R3      R4
        
            Mast S2NABC controls 4 routes; it will display the MOST PERMISSIVE aspect allowed by
            its set of routes.  This can ve visualized as a truth table showing all the possible 
            turnout position combinations:
            
                R1     1   3   5    STOP unless all three turnouts are Normal...
                R2    (1)  -   -    STOP unless Turnout 1 is Reverse
                R3     1  (3)  -    STOP unless turnout 1 is Normal and Turnout 3 is Reverse
                R4     1   3  (5)   STOP unless turnouts 1 and 3 are Normal and Turnout 5 is Reverse
            
            Note that the turnouts beyond the "other path" of an upstream switch don't impact the route,
            so when SW1 is Reversed, the state of SW3 and SW5 don't matter.
            
            this could be written as follows (ignoring multi-head route/speed signaling aspects...)
            
                <mast name="S2NAB">
                    <route name="R1" doc="mainline through">
                        <switch       name="1" position="N" aspect="CLEAR" />
                        <switch       name="3" position="N" aspect="CLEAR" />
                        <switch       name="5" position="N" aspect="CLEAR" />
                        ...
                    </route>
                    <route name="R2" doc="first industry">
                        <switch       name="1" position="R" aspect="DIVERGING" />
                        ...
                    </route>
                    <route name="R3" doc="second industry">
                        <switch       name="1" position="N" aspect="CLEAR" />
                        <switch       name="3" position="R" aspect="DIVERGING" />
                        ...
                    </route>
                    <route name="R4" doc="north siding">
                        <switch       name="1" position="N" aspect="CLEAR" />
                        <switch       name="3" position="N" aspect="CLEAR" />
                        <switch       name="5" position="D" aspect="DIVERGING" />
                        ...
                    </route>
                </mast>
                                                          
        In addition to the switches that define the route, track occupancy along - or beyond - the
        route impacts route availability and locking, and the state of the signal itself (at stop,
        or cleared left or right movement...) also impact the aspect displayed:

        <signals>
            <signal name="904" ER="False" FLEET="False" doc="Departure Track to/from LOOP">
                 <mast name="NA" doc="Northbound LOOP to Departure Track">
                    <route name="LOOP-DT" doc="Northbound LOOP to Departure Track (usual route)">
                        <switch       name="901"                         position="N"              aspect="CLEAR" />
                        <trackcircuit name="901T1" />
                        <trackcircuit name="DAT" />
                        <signal       name="904"                         direction="LEFT"/>
                    </route>
                </mast>
        
                <mast name="SAB"   doc="Southbound on Departure Track (reverse running) to LOOP or YLAD">
                    <route name="RDT-LOOP" doc="Southbound (reverse running) to LOOP">
                        <switch       name="901"                         position="N"               aspect="RESTRICTING" />
                        <trackcircuit name="901T1" />
                        <trackcircuit name="LOOP" />
                        <signal       name="904"                         direction="RIGHT"/>
                    </route>
                    <route name="RDT-Y-LOOP" doc="Southbound on Departure Track (reverse running) to Yard Ladder to LOOP">
                        <switch       name="901"                         position="R"               aspect="DIVERGING_RESTRICTING" />
                        <switch       name="903"                         position="N"               aspect="DIVERGING_RESTRICTING" />
                        <switch       name="905"                         position="N"               aspect="DIVERGING_RESTRICTING" />
                        <switch       name="907"                         position="N"               aspect="DIVERGING_RESTRICTING" />
                        <switch       name="909"                         position="N"               aspect="DIVERGING_RESTRICTING" />
                        <trackcircuit name="901T1" />
                        <section      name="YLAD" />
                        <trackcircuit name="LOOP" />
                        <signal       name="902"                         direction="RIGHT"/>
                        <signal       name="904"                         direction="RIGHT"/>
                    </route>
                </mast>
             </signal>
        </signals>

        Signal Attributes Required:
            'name'          # <even ordinal number>
        Signal Attributes Optional:
            'ER'            # Default: False
            'FLEET'         # Default: False
            'doc'           # Default: None
            'knockdown'     # list of Sections and/or TCs that, if OCCUPIED, causes the signal to fall back to STOP
        
            Mast Attributes Required:
                'name'          # <signalname><direction><heads>    such as 902NAB or 904SA
            Mast Attributes Optional:
                'doc'           # Default: None
                
                Route Attributes Required:
                    'name'          # <unique text>
                Route Attributes Optional:
                    'doc'           # Default: None
                    
                Route Elements Optional (at least 1 is required)
                    APPLIANCE (name, required state, aspect if state is matched) =>
                        if (state == required state) return aspect else return STOP
                        the ASPECT attribute defaults to CLEAR
                    The state of a route is the LEAST PERMISSIVE of all the appliances in that route
                    Example:
                    
                    <mast name="904SAB"   doc="Southbound on Departure Track (reverse running) to LOOP or YLAD">
                        <route name="RDT-LOOP" doc="Southbound (reverse running) to LOOP">
                            <switch       name="901"    position="N"  aspect="RESTRICTING" />
                            <trackcircuit name="901T1" />
                            <trackcircuit name="LOOP"  />
                            <indication   name="CP_WatsonvilleNorth:DAT" />
                            <signal       name="904"    direction="RIGHT"/>
                        </route>   
                                        
                        
                   Example logic flow: 
                        ROUTE = CLEAR # unless something in the route equation makes it less so...
                        if (SW901  is N)          then ROUTE = (most restrictive of (ROUTE, DIVERGING_RESTRICTING) else ROUTE=STOP
                        if (901T1  is UNOCCUPIED) then ROUTE = (most restrictive of (ROUTE, CLEAR)                 else ROUTE=STOP
                        if (LOOP   is UNOCCUPIED) then ROUTE = (most restrictive of (ROUTE, CLEAR)                 else ROUTE=STOP
                        if (SIG904 is RIGHT)      then ROUTE = (most restrictive of (ROUTE, CLEAR)                 else ROUTE=STOP
                        return ROUTE
        '''

        for p in self.root.iterfind("signals"):
            for c in p.iterfind('signal'):
                this  = SIG_Appliance(self.name, c)
                self.appliances.add(this, self.appliances.sig)

                for k in c.iterfind('knockdown'):
                    for tc in k.iterfind('trackcircuit'):
                        this.knockdown.add(TC_Appliance(self.name, tc))
                    for tc in k.iterfind('section'):
                        this.knockdown.add(Section_Appliance(self.name, tc))

                signalname = c.attrib['name']

                for m in c.iterfind('mast'):
                    mastname = m.attrib['name']
                    if not mastname.startswith(signalname):
                        m.attrib['name'] = '{}{}'.format(signalname, mastname)
                        # print('RENAME: Signal {} Mast {} becomes {}'.format(signalname, mastname, m.attrib['name']))

                    mast = MAST_Appliance(self.name, m)
                    this.mast.add(mast)

                    for r in m.iterfind('route'):
                        route = Route(self.name, r)
                        route.sig=this
                        mast.route.add(route)
                        for tc in r.iterfind('trackcircuit'):
                            route.add(TC_Appliance(self.name, tc))
                        for section in r.iterfind('section'):
                            route.add(Section_Appliance(self.name, section))
                        for sw in r.iterfind('switch'):
                            route.add(SW_Route(self.name, sw))
                        for sg in r.iterfind('signal'):
                            route.add(SIG_Route(self.name, sg))
                        for ind in r.iterfind('indication'):
                            route.add(IND_Route(self.name, ind))

        # Dig deeper:  field assignments

        self.field     = SimpleList(self.name, None, "FieldList")
        for p in self.root.iterfind("field"):
            fieldname = p.attrib['name']
            myfield   = FieldUnit(self.name, fieldname)

            self.field.add(myfield)
            '''
                <turtle name="901" device="0" startbit="0" numbits="4" />

                <input   name="901RW"      device="0" bit="0"  />  <!-- Turtle 901 -->
                <input   name="901NW"      device="0" bit="1"  />
                <input   name="901T1"      device="0" bit="2"  />
                <output  name="T901"       device="0" bit="3"  />
            '''
            for xml in p.iterfind("turtle"):
                name     = xml.attrib.get('name')
                device   = xml.attrib.get('device')
                startbit = xml.attrib.get('bit')
                nw = etree.Element("xml", name="{}NW".format(name), device=device, bit=str(int(startbit) + 0))
                rw = etree.Element("xml", name="{}RW".format(name), device=device, bit=str(int(startbit) + 1))
                td = etree.Element("xml", name="{}T1".format(name), device=device, bit=str(int(startbit) + 2))
                t  = etree.Element("xml", name="T{}". format(name), device=device, bit=str(int(startbit) + 3))

                myfield.add(Input(self.name, fieldname, nw))
                myfield.add(Input(self.name, fieldname, rw))
                myfield.add(Input(self.name, fieldname, td))
                myfield.add(Output(self.name, fieldname, t))

            for xml in p.iterfind("trackpower"):
                name     = xml.attrib.get('name')
                device   = xml.attrib.get('device')
                startbit = xml.attrib.get('bit')
                nw = etree.Element("xml", name="{}SHORT".format(name), device=device, bit=str(int(startbit) + 0))
                rw = etree.Element("xml", name="{}TON".  format(name), device=device, bit=str(int(startbit) + 1))
                td = etree.Element("xml", name="{}OCC".  format(name), device=device, bit=str(int(startbit) + 2))
                t  = etree.Element("xml", name="{}OFF".  format(name), device=device, bit=str(int(startbit) + 3))

                myfield.add(Input( self.name, fieldname, nw))
                myfield.add(Input( self.name, fieldname, rw))
                myfield.add(Input( self.name, fieldname, td))
                myfield.add(Output(self.name, fieldname, t))

            for c in p.iterfind("input"):
                myfield.add(Input(self.name, fieldname, c))

            for c in p.iterfind("output"):
                myfield.add(Output(self.name, fieldname, c))

            for c in p.iterfind("expander"):
                myfield.expanders.add(Expander(self.name, fieldname, c))

            for a in p.iterfind("signal"):
                sigMast = SignalMast(self.name, fieldname, a)
                sig     = self.getSig('{}:{}'.format(self.name, sigMast.name))
                if sig is None:
                    print("Error parsing CP XML: Field {} references signal {}, but no such signal is defined.".format(fieldname, sigMast.name))
                    return
                sigMast.sig = sig
                myfield.signals.add(sigMast)

                for m in a.iterfind("mast"):
                    masthead = SignalMastHead(self.name, fieldname, m)
                    sigMastHead = sig.getMast('{}:{}'.format(self.name, masthead.name))
                    if sigMastHead is None:
                        print("Error parsing CP XML: Field {} defines signal {} mast {}, but no such signal mast is defined.".format(
                            fieldname, sigMast.name, masthead.name))
                        return
                    masthead.sighead = sigMastHead
                    for c in m.iterfind('output'):
                        io = Output(self.name, fieldname, c)
                        masthead.field.add(io)
                        myfield.add(io)
                    sigMast.add(masthead)

        self.indications.sort()
        for d in self.depends:
            d.indications.sort()
            d.controls.sort()

        self.controls.sort()
        self.field.sort()

        # generate initialization strings for io expanders
        for k,v in self.FieldunitList():
            v.expanders.sort()
            v.expanders.generate()


    ''' 
    Convenience accessor functions called from MAKO template embedded code
    
    The "cp" object is the only data item provided to the template rendering environment
    '''

    def order(self, l):
        return iter(natsorted(l))

    def define(self, a, b):
        return '#define {:<35}\t{}'.format(a, b)

    def getFQBN(self):
        return self.FQBN

    def getNode(self):
        return self.node

    def getNodeName(self):
        return 'NODE_{}'.format(cp.name.upper())

    def getDependencyList(self):
        yield cp
        for d in cp.depends:
            for k, v in d.indications.children.items():
                yield (k, v)

    def getControlsList(self):
        for k, v in cp.controls.children.items():
            yield (k, v)

    def getIndicationsList(self):
        for k, v in cp.indications.children.items():
            yield (k, v)

    def getFieldUnitList(self):
        for k, v in cp.field.children['fieldunit'].children.items():
            yield (k, v)

    def getExpanderList(self):
        for k, v in cp.field.children['fieldunit'].expanders.children.items():
             yield (k, v)

    def getTrackCircuitList(self):
        for k, v in iter(natsorted(self.appliances.tc.items())):
            yield (k, v)

    def getSectionList(self):
        for k, v in iter(natsorted(self.appliances.sections.items())):
            yield (k, v)

    def getMaintainerCallList(self):
        for k, v in iter(natsorted(self.appliances.mc.items())):
            yield (k,v)

    def getTrackPowerList(self):
        for k, v in iter(natsorted(self.appliances.trackpower.items())):
            yield (k,v)

    def getSwitchList(self):
        for k, v in iter(natsorted(self.appliances.sw.items())):
            yield (k,v)

    def getSigList(self):
        for k, v in iter(natsorted(self.appliances.sig.items())):
            yield (k,v)

    def HeadList(self):
        for k, v in iter(natsorted(self.appliances.sig.items())):
            for hk, hv in iter(natsorted(v.mast.children.items())):
                yield (hk,hv)

    def DocList(self):
        for d in self.documentation:
            yield d

    def FieldunitList(self):
        for k, v in self.field.children.items():
            yield (k,v)

    def today(self):
        return datetime.datetime.today().strftime('%Y-%m-%d %H:%M')


def extant_file(x):
    """
    'Type' for argparse - checks that file exists but do not open it
    """
    if not os.path.exists(x):
        raise argparse.ArgumentError("{0} does not exist".format(x))
    return x

def write_template(args, dirname, fname):
    # print("Template:  using {}".format(args.templatename[0]))
    tm = Template(filename=args.templatename[0])
    result = tm.render(args=args, cp=cp)
    # remove empty lines
    lines = result.splitlines()
    clean_result = ""
    sep = ''
    for line in lines:
        cleanline = line.rstrip()
        if cleanline != '':
            clean_result = clean_result + sep + line
            sep = "\n"
            if line == '}':
                clean_result = clean_result + '\n'
    clean_result = clean_result + '\n'
    #write_sketch(dirname, fname, clean_result)
    write_sketch(dirname, fname, result)


def write_sketch(dirname, fname, contents):
    if not dirname:
        dirname = "."
    if not fname:
        print("... exiting")
        sys.exit(-3)
    if dirname and not os.path.exists(dirname):
        os.makedirs(dirname)
    #print("# Writing {count} lines to {name}".format(count=contents.count("\n"), name=dirname + '/' + fname), file=sys.stderr)
    outfile=open(dirname + '/' + fname, 'w') if fname != "-" else sys.stdout
    outfile.write(contents)
    outfile.close()


if __name__ == "__main__":
    fname = ""
    parser = argparse.ArgumentParser(description='Generate code for a control point')
    parser.add_argument("-i", "--input",
        dest="filename", required=True, type=extant_file,
        help="input XML file with control point definition", metavar="FILE")
    parser.add_argument("-o", "--outfile",  dest="outfilename", nargs=1)
    parser.add_argument("-T", "--Template", dest="templatename", nargs=1)
    parser.add_argument('--type',           dest="type", choices=['html', 'md', 'ctc', 'decoder', 'jmri', 'sketch', 'json', 'template'])
    parser.add_argument('--codeline',       dest="codeline", choices=['loconet', 'coap', 'mqtt'])
    args = parser.parse_args()

    if args.type == "html" \
            or args.type == "md" \
            or args.type == "decoder" \
            or args.type == "jmri" \
            or args.type == "sketch" \
            or args.type == "json" \
            or args.type == "ctc" \
            or args.type == "template" :
        # print('Reading definition from "{}"'.format(args.filename))
        d = os.path.dirname(args.filename)
        f = os.path.basename(args.filename)
        cp = ControlPoint(d, f, None)

        myname = cp.name
        layout = cp.layout

        if not args.outfilename :
            if args.type == "decoder":
                f = ("{cp}.py").format(cp=myname)
            elif args.type == "jmri":
                f = ("createPanel_{cp}.sh").format(cp=myname)
            elif args.type == "html":
                f = ("{cp}.html").format(cp=myname)
            elif args.type == "md":
                f = ("{cp}.md").format(cp=myname)
            elif args.type == "sketch":
                f = ("{cp}.cc").format(cp=myname)
            elif args.type == "json":
                f = ("sketch.json").format(cp=myname)

        elif args.outfilename[0] == '-':      # stdout...
            f = '-'
            d = ''
        elif args.outfilename[0][0] == '/': # fully qualified...
            f = os.path.basename(args.outfilename[0])
            d = os.path.dirname(args.outfilename[0])
        else:                                                 # relative, put in Auto dir...
            if args.outfilename[0].find('/') != -1:
                f = os.path.basename(args.outfilename[0])
                d = './' + os.path.dirname(args.outfilename[0])
            else:
                f=args.outfilename[0]
                d='./'

        if args.type == 'template':
            if args.templatename is None:
                print('Error:  --type template requires a -T TEMPLATENAME')
                sys.exit(-1)
            write_template(args, d, f)
        elif args.type == 'html':
            if args.templatename is None:
                args.templatename = ["mako_templates/html.template.mako"]
            write_template(args, d, f)
        elif args.type == 'md':
            if args.templatename is None:
                args.templatename = ["mako_templates/md.template.mako"]
            write_template(args, d, f)
        elif args.type == 'jmri':
            if args.templatename is None:
                args.templatename = ["mako_templates/jmri.template.mako"]
            write_template(args, d, f)
        elif args.type == 'decoder':
            if args.templatename is None:
                args.templatename = ["mako_templates/codelineDecoder.template.mako"]
            write_template(args, d, f)
        elif args.type == 'sketch':
            if args.templatename is None:
                args.templatename = ["mako_templates/fieldsketch.template.mako"]
            write_template(args, d, f)
        elif args.type == 'json':
            if args.templatename is None:
                args.templatename = ["mako_templates/sketch.json.mako"]
            write_template(args, d, 'sketch.json')
        elif args.type == 'ctc':
            if args.templatename is None:
                args.templatename = ["mako_templates/ctcPanel.template.mako"]
            write_template(args, d, f)


    else :
        print("Error: no type specified")
        sys.exit(-2)
