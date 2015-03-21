#!/usr/bin/python

import xml.dom.minidom
import sys
from collections import OrderedDict
import json


def defineSW(sw, controlpoint, DOM):
    id = DOM.getAttribute("name")
    me = {}
    me["name"] = controlpoint + "_SW" + id
    # print "defining: " + me["name"]
    me["tc"] = DOM.getAttribute("trackcircuit")
    me["tcname"] = controlpoint + "_" + DOM.getAttribute("trackcircuit")
    #if (me["tc"]):
    #    t = {}
    #    t["name"] = controlpoint + "_" + me["tc"]
    #    tc[me["tc"]] = t
    i = {}
    i["normal"]      = "K" + id + "NW"
    i["reverse"]     = "K" + id + "RW"
    i["normalname"]  = controlpoint + "_K" + id + "NW"
    i["reversename"] = controlpoint + "_K" + id + "RW"
    me["indication"] = i
    c = {}
    c["normal"]      = "S" + id + "NW"
    c["reverse"]     = "S" + id + "RW"
    c["normalname"]  = controlpoint + "_S" + id + "NW"
    c["reversename"] = controlpoint + "_S" + id + "RW"
    me["control"]    = c
    f = {}
    f["normal"]      =  ""  + id  + "NW"
    f["reverse"]     =  ""  + id  + "RW"
    f["motor"]       =  "T" + id
    f["normalname"]  =  "F"  + id  + "NW"
    f["reversename"] =  "F"  + id  + "RW"
    f["motorname"]   =  "FT" + id
    me["field"] = f
    sw[id] = me

def defineTC(tc, controlpoint, DOM):
    id = DOM.getAttribute("name")
    me = {}
    me["name"]            = controlpoint + "_" + id
    me["indication"]      = "K" + id
    me["indication_name"] = controlpoint + "_K" + id
    me["field"]           = "F" + id
    me["fieldname"]       = controlpoint + "_F" + id
    # print "defining: " + me["name"]
    tc[id] = me


def defineMC(mc, controlpoint, DOM):
    id = DOM.getAttribute("name")
    me = {}
    me["name"]            = controlpoint + "_" + id
    me["indication"]      = "K" + id
    me["indicationname"]  = controlpoint + "_K" + id
    me["field"]           = "F" + id
    me["fieldname"]       = controlpoint + "_F" + id
    me["control"]         = "S" + id
    me["controlname"]     = controlpoint + "_S" + id
    # print "defining: " + me["name"]
    mc[id] = me


def defineSIG(sig, controlpoint, DOM):
    id = DOM.getAttribute("name")
    me = {}
    me["name"] = controlpoint + "_SIG" + id
    # print "defining: " + me["name"]
    i = {}
    i["north"]     = "K" + id + "NG"
    i["south"]     = "K" + id + "SG"
    i["northname"] = controlpoint + "_K" + id + "NG"
    i["southname"] = controlpoint + "_K" + id + "SG"
    me["indication"] = i
    c = {}
    c["north"]     = "S" + id + "NG"
    c["south"]     = "S" + id + "SG"
    c["stop"]      = "S" + id + "H"
    c["northname"] = controlpoint + "_S" + id + "NG"
    c["southname"] = controlpoint + "_S" + id + "SG"
    c["stopname"]  = controlpoint + "_S" + id + "H"
    me["control"] = c
    heads = []
    DOMheads = DOM.getElementsByTagName("head")
    for h in DOMheads:
        hn=h.getAttribute("name")
        heads.append(hn)
        me[hn+"name"] = controlpoint + "_" + hn
    me["heads"] = heads
    sig[id] = me


def defineIND(ind, controlpoint, DOM):
    id = DOM.getAttribute("name")
    me = {}
    me["name"]            = controlpoint + "_" + id
    me["indication"]      = "K" + id
    me["indicationname"]  = controlpoint + "_K" + id
    me["byte"] = int(DOM.getAttribute("byte"))
    me["bit"]  = int(DOM.getAttribute("bit"))
    ind[id] = me

def defineCTL(ctl, controlpoint, DOM):
    id = DOM.getAttribute("name")
    me = {}
    me["name"]        = controlpoint + "_" + id
    me["control"]     = "S" + id
    me["controlname"] = controlpoint + "_S" + id
    me["byte"] = int(DOM.getAttribute("byte"))
    me["bit"]  = int(DOM.getAttribute("bit"))
    ctl[id] = me


def defineIO(field, controlpoint, DOM, io):
    global sig
    id = DOM.getAttribute("name")
    if DOM.hasAttribute("byte"):
        me = {}
        me["name"]      = controlpoint + "_F" + id
        me["field"]     = "F" + id
        me["fieldname"] = controlpoint + "_F" + id
        me["byte"] = int(DOM.getAttribute("byte"))
        me["bit"]  = int(DOM.getAttribute("bit"))
        me["io"]   = io
        field[id] = me
    else:
        DOMheads = DOM.getElementsByTagName("output")
        olist=[]
        for hDOM in DOMheads:
            h_id = hDOM.getAttribute("name")
            minime = {}
            minime["name"] = controlpoint + "_" + h_id
            minime["field"]= "F" + h_id
            minime["byte"] = int(hDOM.getAttribute("byte"))
            minime["bit"]  = int(hDOM.getAttribute("bit"))
            minime["io"]   = io
            field[h_id] = minime
            olist.append(h_id)
        for s in sig:
            if id in sig[s]["heads"]:
                #print "adding ", str(olist), " to "
                sig[s][id] = olist

def defineEXP(exp, controlpoint, DOM):
    me = {}
    id = "IOExpander" + DOM.getAttribute("byte") + "_" + DOM.getAttribute("type") + "_" + DOM.getAttribute("address")
    me["name"] = controlpoint + "_" + id
    me["type"] = DOM.getAttribute("type")
    me["address"] = DOM.getAttribute("address")
    me["byte"] = int(DOM.getAttribute("byte"))
    exp[id] = me


def generateDefinitions(myhash, numbytes):
    a = [[0 for x in range(8)] for x in range(numbytes)]
    for k, v in myhash.items():
        # print "Key: ", k, "VALUE: ", v
        byte = v["byte"]
        bit = v["bit"]
        if "io" in v:
            k = v["io"] + '_' + myhash[k]["field"]
        a[byte][bit] = k
    return a


def generateExpander(myhash, myfield, numbytes):
    a = [0 for x in range(numbytes)]  # array of expanders
    bits = [0 for x in range(numbytes)]  # array of expander initializations
    # walk thru the field bits and gather up the i/o directions for expander initialization
    for byte in range(numbytes):
        bits[byte] = ''
        empty = 1
        for bit in range(8):
            if not isinstance(myfield[byte][bit], int):
                empty = 0
        if not empty:
            for bit in range(8):
                v = myfield[byte][bit]
                if (isinstance(v, int)):
                    v = 'O_'
                if (v[1] == '_') and ((v[0] == 'I') or (v[0] == 'O')):
                    v = '0' if v[:1] == 'O' else '1'
                bits[byte] = bits[byte] + v
        if bits[byte] == '': bits[byte] = '00000000'
        # print "init[" + str(byte) + "] = " + bits[byte]
    for k, v in sorted(myhash.iteritems(), key=lambda (k, v): v['byte']):
        # print "Key: ", k, "VALUE: ", v
        byte = v["byte"]
        type = v["type"]
        addr = v["address"]
        me = {}
        me["name"] = "IOexpander_" + str(byte)
        me["type"] = type
        me["address"] = addr
        me["init"] = bits[byte]
        me["code"] = "m[" + str(byte) + "].init(" + addr + ", I2Cextender::" + type + "," + '\tB' + bits[byte] + ");"
        a[byte] = me
    return a


def printTable(a, tablename, cpname, numbytes):
    sys.stdout.write(' *        ' + tablename + ' for ' + cpname + '\n')
    sys.stdout.write(' *        +---------+---------+---------+---------+---------+---------+---------+---------+\n')
    prepend = ' *        | '
    for bit in range(8):
        sys.stdout.write(prepend)
        prepend = '| '
        v = 'bit ' + str(bit)
        sys.stdout.write(v)
        for filler in range(len(v), 8):
            sys.stdout.write(' ')
    sys.stdout.write('|\n')
    sys.stdout.write(' *        +---------+---------+---------+---------+---------+---------+---------+---------+\n')
    for byte in range(numbytes):
        empty = 1
        for bit in range(8):
            if not isinstance(a[byte][bit], int):
                empty = 0
        if not empty:
            sys.stdout.write(' * Byte ' + str(byte) + ' | ')
            prepend = ''
            for bit in range(8):
                sys.stdout.write(prepend)
                prepend = '| '
                v = a[byte][bit]
                if (isinstance(v, int)):
                    v = '- - - -'
                if (v[1] == '_') and ((v[0] == 'I') or (v[0] == 'O')):
                    v = v[:1].lower() + ' ' + v[2:]
                sys.stdout.write(v)
                for filler in range(len(v), 8):
                    sys.stdout.write(' ')
            sys.stdout.write('|\n')
    sys.stdout.write(' *        +---------+---------+---------+---------+---------+---------+---------+---------+\n')


def printExpander(expandertable, tablename, cpname, numbytes):
    sys.stdout.write(' *        ' + tablename + ' for ' + cpname + '\n')
    sys.stdout.write(' *        +-------------------------------------------------------------------------------+\n')
    for byte in range(numbytes):
        me = expandertable[byte]
        if me:
            sys.stdout.write(' * Byte ' + str(byte) + ' | ')
            sys.stdout.write(
                me["type"] + "\tChip Address: " + me["address"] + "\tI/O Map: B" + me["init"] + "\t(1=input, 0=output)\t  |\n")
    sys.stdout.write(' *        +-------------------------------------------------------------------------------+\n')


def init(controlpoint):
    global cpname
    global layoutname
    global nodenumber
    global sw, tc, mc, sig, ind, ctl, field, exp
    global indicationtable
    global controltable
    global fieldtable
    global expandertable

    if controlpoint.hasAttribute("name"):
        cpname = controlpoint.getAttribute("name")
    if controlpoint.hasAttribute("layout"):
        layoutname = controlpoint.getAttribute("layout")
    if controlpoint.hasAttribute("node"):
        nodenumber = controlpoint.getAttribute("node")

    # Get all the components in the controlpoint
    DOMswitches = controlpoint.getElementsByTagName("switch")
    DOMtrackcircuits = controlpoint.getElementsByTagName("trackcircuit")
    DOMmaintainers = controlpoint.getElementsByTagName("call")
    DOMsignals = controlpoint.getElementsByTagName("signal")
    DOMindications = controlpoint.getElementsByTagName("indication")
    DOMcontrols = controlpoint.getElementsByTagName("control")
    DOMinputs = controlpoint.getElementsByTagName("input")
    DOMoutputs = controlpoint.getElementsByTagName("output")
    DOMexpanders = controlpoint.getElementsByTagName("expander")

    for item in DOMswitches:
        defineSW(sw, cpname, item)
    for item in DOMtrackcircuits:
        defineTC(tc, cpname, item)
    for item in DOMmaintainers:
        defineMC(mc, cpname, item)
    for item in DOMsignals:
        defineSIG(sig, cpname, item)
    for item in DOMindications:
        defineIND(ind, cpname, item)
    for item in DOMcontrols:
        defineCTL(ctl, cpname, item)
    for item in DOMinputs:
        defineIO(field, cpname, item, "I")
    for item in DOMoutputs:
        if (not item.getAttribute("bits")):  # skip
            defineIO(field, cpname, item, "O")
    for item in DOMexpanders:
        defineEXP(exp, cpname, item)

    field = OrderedDict(sorted(field.items(), key=lambda (k, v): (v['byte'] * 8 + v['bit']) ))
    ind   = OrderedDict(sorted(ind.items(),   key=lambda (k, v): (v['byte'] * 8 + v['bit']) ))
    ctl   = OrderedDict(sorted(ctl.items(),   key=lambda (k, v): (v['byte'] * 8 + v['bit']) ))
    tc    = OrderedDict(sorted(tc.items(),    key=lambda (k, v): v['name'] ))
    mc    = OrderedDict(sorted(mc.items(),    key=lambda (k, v): v['name'] ))
    sw    = OrderedDict(sorted(sw.items(),    key=lambda (k, v): v['name'] ))
    sig   = OrderedDict(sorted(sig.items(),   key=lambda (k, v): v['name'] ))
    exp   = OrderedDict(sorted(exp.items(),   key=lambda (k, v): v['name'] ))

    indicationtable = generateDefinitions(ind, 8)
    controltable = generateDefinitions(ctl, 8)
    fieldtable = generateDefinitions(field, 18)
    expandertable = generateExpander(exp, fieldtable, 18)


def printBold(pre, s, c, overhang):
    l = len(s)
    sys.stdout.write(pre)
    for filler in range(l + overhang * 2):
        sys.stdout.write(c)
    sys.stdout.write('\n')
    sys.stdout.write(pre)
    for filler in range(overhang):
        sys.stdout.write(' ')
    sys.stdout.write(s + '\n')
    sys.stdout.write(pre)
    for filler in range(l + overhang * 2):
        sys.stdout.write(c)
    sys.stdout.write('\n')


def printInclude(file):
    print "#include <" + file + ">"


def M(name):
    return (cpname.upper() + "_" + name)

# -------------------------------------------------------------------------------
cpname          = "undefined"
layoutname      = "myLayout"
nodenumber      = "0x01"
sw = {}
tc = {}
mc = {}
sig = {}
ind = {}
ctl = {}
field = {}
exp = {}
indicationtable = []
controltable    =  []
fieldtable      =  []
expandertable   =  []

# Open XML document using minidom parser
DOMTree = xml.dom.minidom.parse("cp_christopher.xml")
controlpoint = DOMTree.documentElement
init(controlpoint)

print "/*"
print " *  Autogenerated Control Point code for"
print " *"
printBold(" *  ", cpname + " Field Unit", "*", 2)
print " *"
print " *"
print " *  Copyright 2013-2015 John Plocher "
print " *  Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)"
print " *"
printTable(controltable, 'Control Packet', cpname, 8)
print " *"
printTable(indicationtable, 'Indication Packet', cpname, 8)
print " *"
printTable(fieldtable, 'Physical IO', cpname, 18)
print " *"
printExpander(expandertable, 'I2C Expanders', cpname, 18)
print " *"
print " */"
print ""
printInclude("Arduino.h")
printInclude("EEPROM.h")
printInclude("Wire.h")
printInclude("LocoNet.h")
printInclude("I2CExtender.h")
printInclude("elapsedMillis.h")
printInclude(layoutname + ".h")
print ""
print "#define ME      \"" + cpname + "\""
print "#define NODE_" + cpname.upper() + "\t" + str(nodenumber)
print ""
print "#define NODE_ME NODE_" + cpname.upper()
print ""
print "#define " + M("PORTS") + "\t" + str(len(exp))
print "#define LNET_TX_PIN  7"
print "#define LNET_RX_PIN  8"
print ""
print "int getNumPorts(void)          { return (" + str(len(exp)) + "); }"
print "int getNumTrackCircuits(void)  { return (" + str(len(tc)) + "); }"
print "int getNumSwitches(void)       { return (" + str(len(sw)) + "); }"
print "int getNumSignals(void)        { return (" + str(len(sig)) + "); }"
numheads = 0;
for item in sig:
    numheads += len(sig[item]["heads"])
print "int getNumHeads(void)          { return (" + str(numheads) + "); }"
print "int getNumCalls(void)          { return (" + str(len(mc)) + "); }"

print ""
print "I2Cextender m[" + M("PORTS") + "];"
print ""

def printApplianceDefines(dict):
    counter = 0
    for x in dict:
        print "#define " + str(dict[x]["name"]) + "\t" + str(counter)
        counter += 1
def printCodelineDefines(dict):
    for x in dict:
        print "#define " + str(dict[x]["name"]) + "\t" + str(int(dict[x]["byte"]) * 8 + int(dict[x]["bit"]))

print "// Appliances (TrackCircuits, Switches, Maintainers, Signals and Heads)"
printApplianceDefines(tc)
printApplianceDefines(sw)
printApplianceDefines(mc)
printApplianceDefines(sig)
counter=0
for item in sig:
    h=sig[item]["heads"]
    for x in h:
        print "#define "+ sig[item][str(x)+"name"] + "\t" + str(counter)
        counter += 1
print ""
print "// Controls"
printCodelineDefines(ctl)
print ""
print "// Indications"
printCodelineDefines(ind)
print ""
print "// Field"
printCodelineDefines(field)
print '''
#define toBit(x)    ((x) % 8)
#define toByte(x)   ((x) / 8)
'''
print "TrackCircuit track[" + str(len(tc)) + "] = {"
for x in tc:
    f=str(tc[x]["field"])
    print("\tTrackCircuit(\"" + x + "\",\t&m[" + str(field[x]["byte"]) + "],\t" + str(field[x]["bit"]) + ")," +
        "\t\t\t// " + str(tc[x]["name"]) )
print "};"
print "Switch sw[" + str(len(sw)) + "] = {"
for x in sw:
    f=sw[x]["field"]
    nf=str(f["normal"])
    rf=str(f["reverse"])
    mf=str(f["motor"])
    sys.stdout.write("\tSwitch(\"" + x + "\",\t\t")
    sys.stdout.write("&m[" + str(field[nf]["byte"]) + "],\t" )
    sys.stdout.write(str(field[nf]["bit"]) + ".\t" )
    sys.stdout.write(str(field[rf]["bit"]) + ",\t" )
    sys.stdout.write(str(field[mf]["bit"]) + ")," )
    sys.stdout.write("\t// " + str(sw[x]["name"]) )
print "};"
print "Maintainer mc[" + str(len(mc)) + "] = {"
for x in mc:
    f=str(mc[x]["field"])
    print("\tMaintainer(\"" + x + "\",\t&m[" + str(field[x]["byte"]) + "],\t" + str(field[x]["bit"]) + ")," +
    "\t\t\t// " + str(mc[x]["name"]) )
print "};"

print "RRSignal sig[" + str(len(sig)) + "] = {"
for x in sig:
    print "\tRRSignal(\"" + x + "\")," + "\t\t\t\t\t\t// " + str(sig[x]["name"])
print "};"

print "RRSignalHead head[" + str(numheads) + "] = {"
for item in sig:
    h=sig[item]["heads"]
    for x in h:
        sys.stdout.write("\tRRSignalHead(\"" + x + "\",\t")
        hlist = sig[item][x]
        pre=0
        for h in hlist :
            if not pre :
                sys.stdout.write("&m[" + str(field[h]["byte"]) + "]")
                pre=",\t"
            sys.stdout.write(pre + str(field[h]["bit"]))
        print "};" + "\t\t// "+ sig[item][str(x)+"name"]
print "};"



print '''
void initI2Cextender( I2Cextender *m ) {
        Wire.begin();

        for (int x = 0; x < getNumPorts(); x++) {
            m[x]       = I2Cextender();
        }
'''
for i, item in enumerate(expandertable):
    if item: print "\t" + item["code"]
print "};"


print '''
/*
 *  Routes 
 */
// Aspect for head "A" on 2S... (the mast has 2 heads, "A" over "B")
// If top head is not STOP, bottom head should be STOP and vice-versa
int A_2SA() {
    // calculate the aspects suitable for each of the various routes thru the interlocking/control point
    RRSignalHead::Aspects r1 = RRSignalHead::CLEAR;
    RRSignalHead::Aspects r2 = RRSignalHead::STOP;    //    MT2 N'bound crossover to MT1:
    //    MT2 N'bound on MT2: 
    r1 = RRSignalHead::mostRestrictive(r1, sw[CP_Christopher_SW3]   .is(Switch::NORMAL)      ? RRSignalHead::CLEAR    : RRSignalHead::STOP);
    r1 = RRSignalHead::mostRestrictive(r1, track[CP_Christopher_3T2].is(TrackCircuit::EMPTY) ? RRSignalHead::CLEAR    : RRSignalHead::STOP);
    r1 = RRSignalHead::mostRestrictive(r1, track[CP_Christopher_WA1].is(TrackCircuit::EMPTY) ? RRSignalHead::CLEAR    : RRSignalHead::STOP);
    return RRSignalHead::leastRestrictive(r1, r2);
}
int A_2SB() {
    RRSignalHead::Aspects r1 = RRSignalHead::STOP;   //    MT2 N'bound on MT2: 
    RRSignalHead::Aspects r2 = RRSignalHead::CLEAR;
    
    //    MT2 N'bound crossover to MT1:
    r2 = RRSignalHead::mostRestrictive(r2, sw[CP_Christopher_SW3]   .is(Switch::REVERSE)     ? RRSignalHead::APPROACH : RRSignalHead::STOP);
    r2 = RRSignalHead::mostRestrictive(r2, sw[CP_Christopher_SW5]   .is(Switch::NORMAL)      ? RRSignalHead::CLEAR    : RRSignalHead::STOP);
    r2 = RRSignalHead::mostRestrictive(r2, track[CP_Christopher_3T2].is(TrackCircuit::EMPTY) ? RRSignalHead::CLEAR    : RRSignalHead::STOP);
    r2 = RRSignalHead::mostRestrictive(r2, track[CP_Christopher_3T1].is(TrackCircuit::EMPTY) ? RRSignalHead::CLEAR    : RRSignalHead::STOP);
    r2 = RRSignalHead::mostRestrictive(r2, track[CP_Christopher_5T1].is(TrackCircuit::EMPTY) ? RRSignalHead::CLEAR    : RRSignalHead::STOP);
    r2 = RRSignalHead::mostRestrictive(r2, track[CP_Christopher_WA2].is(TrackCircuit::EMPTY) ? RRSignalHead::CLEAR    : RRSignalHead::STOP);
    r2 = RRSignalHead::mostRestrictive(r2, (RRSignalHead::Aspects)sig[CP_Christopher_SIG2]    .RightAspect());
    return RRSignalHead::leastRestrictive(r1, r2);
}

int A_2NA() {
    RRSignalHead::Aspects r1 = RRSignalHead::CLEAR;   //    MT1 S'bound into MT1:
    RRSignalHead::Aspects r2 = RRSignalHead::STOP;    //    MT2 S'bound crossover to MT2:
    RRSignalHead::Aspects r3 = RRSignalHead::CLEAR;   //    MT2 S'bound into IND:
    //    MT1 S'bound into MT1:
    r1 = RRSignalHead::mostRestrictive(r1, sw[CP_Christopher_SW5]   .is(Switch::NORMAL)      ? RRSignalHead::CLEAR      : RRSignalHead::STOP);
    r1 = RRSignalHead::mostRestrictive(r1, sw[CP_Christopher_SW3]   .is(Switch::NORMAL)      ? RRSignalHead::CLEAR      : RRSignalHead::STOP);
    r1 = RRSignalHead::mostRestrictive(r1, sw[CP_Christopher_SW1]   .is(Switch::NORMAL)      ? RRSignalHead::CLEAR      : RRSignalHead::STOP);
    r1 = RRSignalHead::mostRestrictive(r1, track[CP_Christopher_5T1].is(TrackCircuit::EMPTY) ? RRSignalHead::CLEAR      : RRSignalHead::STOP);
    r1 = RRSignalHead::mostRestrictive(r1, track[CP_Christopher_3T1].is(TrackCircuit::EMPTY) ? RRSignalHead::CLEAR      : RRSignalHead::STOP);
    r1 = RRSignalHead::mostRestrictive(r1, track[CP_Christopher_EA2].is(TrackCircuit::EMPTY) ? RRSignalHead::CLEAR      : RRSignalHead::STOP);

    //    MT2 S'bound into IND:
    r3 = RRSignalHead::mostRestrictive(r3, sw[CP_Christopher_SW5]   .is(Switch::REVERSE)     ? RRSignalHead::APPROACH   : RRSignalHead::STOP);
    r3 = RRSignalHead::mostRestrictive(r3, sw[CP_Christopher_SW1]   .is(Switch::REVERSE)     ? RRSignalHead::APPROACH   : RRSignalHead::RESTRICTING);
    r3 = RRSignalHead::mostRestrictive(r3, track[CP_Christopher_5T1].is(TrackCircuit::EMPTY) ? RRSignalHead::CLEAR      : RRSignalHead::STOP);
    r3 = RRSignalHead::mostRestrictive(r3, track[CP_Christopher_1T1].is(TrackCircuit::EMPTY) ? RRSignalHead::CLEAR      : RRSignalHead::RESTRICTING);
    return RRSignalHead::leastRestrictive(RRSignalHead::leastRestrictive(r1, r2), r3);
}

int A_2NB() {
    RRSignalHead::Aspects r1 = RRSignalHead::STOP;    //    MT1 S'bound into MT1:
    RRSignalHead::Aspects r2 = RRSignalHead::CLEAR;
    RRSignalHead::Aspects r3 = RRSignalHead::STOP;    //    MT2 S'bound into IND:
    
    //    MT2 S'bound crossover to MT2:
    r2 = RRSignalHead::mostRestrictive(r2, sw[CP_Christopher_SW5]   .is(Switch::NORMAL)      ? RRSignalHead::CLEAR      : RRSignalHead::STOP);
    r2 = RRSignalHead::mostRestrictive(r2, sw[CP_Christopher_SW3]   .is(Switch::REVERSE)     ? RRSignalHead::APPROACH   : RRSignalHead::STOP);
    r2 = RRSignalHead::mostRestrictive(r2, track[CP_Christopher_5T1].is(TrackCircuit::EMPTY) ? RRSignalHead::CLEAR      : RRSignalHead::STOP);
    r2 = RRSignalHead::mostRestrictive(r2, track[CP_Christopher_3T1].is(TrackCircuit::EMPTY) ? RRSignalHead::CLEAR      : RRSignalHead::STOP);
    r2 = RRSignalHead::mostRestrictive(r2, track[CP_Christopher_3T2].is(TrackCircuit::EMPTY) ? RRSignalHead::CLEAR      : RRSignalHead::STOP);
    r2 = RRSignalHead::mostRestrictive(r2, track[CP_Christopher_EA1].is(TrackCircuit::EMPTY) ? RRSignalHead::CLEAR      : RRSignalHead::STOP);
    r2 = RRSignalHead::mostRestrictive(r2, (RRSignalHead::Aspects)sig[CP_Christopher_SIG2]  .LeftAspect());
    return RRSignalHead::leastRestrictive(RRSignalHead::leastRestrictive(r1, r2), r3);
}


boolean processSignals() {
    boolean somethingchanged = false;
    for (int x = 0; x < getNumSignals(); x++) { 
        if (sig[x].runTime() == RRSignal::EXPIRED) {
            sig[x].report();
            somethingchanged = true;
        }
    }
    // knock down signals ...
    if (sw[CP_Christopher_SW3].is(Switch::REVERSE) ) {
        if (track[CP_Christopher_1T1].is(TrackCircuit::OCCUPIED) ||
            track[CP_Christopher_3T1].is(TrackCircuit::OCCUPIED) ||
            track[CP_Christopher_3T2].is(TrackCircuit::OCCUPIED) ||
            track[CP_Christopher_5T1].is(TrackCircuit::OCCUPIED) ) {
              somethingchanged |= sig[CP_Christopher_SIG2].knockdown();
        }
    }
    head[CP_Christopher_H2NA].set((RRSignalHead::Aspects)A_2NA());
    head[CP_Christopher_H2NB].set((RRSignalHead::Aspects)A_2NB());
    head[CP_Christopher_H2SA].set((RRSignalHead::Aspects)A_2SA());
    head[CP_Christopher_H2SB].set((RRSignalHead::Aspects)A_2SB());
    
    return somethingchanged;
}

boolean handleControlPacket(int src, int dst, int *controls, boolean force) {
    boolean cc = false;
    if (src == NODE_ME) {                           // I sent this one...
      	      // Serial.println(" (Ignoring my loopback Indication Packet...)");
    } else if ((src != NODE_CTC) && (src != NODE_LOCAL)) {                   // Don't pay attention to gossip :-)
              // Serial.println(" (Ignoring other unit's Indication Packet...)");
    } else if (dst != NODE_ME) {           // for someone else...
      	      // Serial.println(" (Ignoring other unit's Control Packet...)");
    } else {                                        // for me!
        int safe = true;
        cc = true;

        // Is this a safe command?
        //   Plant must be empty (switches not fouled...)
'''
for x in sw:
    print "\tsafe &= !track[" + str(sw[x]["tcname"]) + "].is(TrackCircuit::OCCUPIED);"
print "\t//   Control packet must make sense"
for x in sw:
    print "\tsafe &= sw[" + str(sw[x]["name"]) + "].isSafe(&controls[" +  sw[x]["control"]["normal"]+ "], , );"

'''
        safe &= !track[CP_Christopher_1T1].is(TrackCircuit::OCCUPIED);
        safe &= !track[CP_Christopher_3T1].is(TrackCircuit::OCCUPIED);
        safe &= !track[CP_Christopher_3T2].is(TrackCircuit::OCCUPIED);
        safe &= !track[CP_Christopher_5T1].is(TrackCircuit::OCCUPIED);
        //   Control packet must make sense
        safe &= sw[CP_Christopher_SW1]  .isSafe(&controls[0], CP_Christopher_S1NW, CP_Christopher_S1RW);
        safe &= sw[CP_Christopher_SW3]  .isSafe(&controls[0], CP_Christopher_S3NW, CP_Christopher_S3RW);
        safe &= sw[CP_Christopher_SW3B] .isSafe(&controls[0], CP_Christopher_S3NW, CP_Christopher_S3RW);
        safe &= sw[CP_Christopher_SW5]  .isSafe(&controls[0], CP_Christopher_S5NW, CP_Christopher_S5RW);

        safe &= sig[CP_Christopher_SIG2].isSafe(bitRead(controls[1], CP_Christopher_S2SG), bitRead(controls[1], CP_Christopher_S2NG));
        
        // can only change FLEET stick and MC lights while plant is occupied
        // There is no MC at this CP
        // TODO: Need to deal with fleet controls
        if (force) safe=1;  // At startup, force the CP to initialize into the last saved state
        if (!safe) {
            // Serial.println("VITAL level plant reject");
            lcd.setCursor(17,  0); lcd.print("VR");
        } else {  // valid control packet...
            lcd.setCursor(17,  0); lcd.print("OK");
            for (int x = 0; x <  getNumSwitches(); x++) {
                sw[x].doSafe();
            }
            for (int x = 0; x <   getNumSignals(); x++) {
                sig[x].doSafe();
            }
            ControlPoint::savestate(controls);  // remember last commanded turnout state in eeprom...
        }
    }
    return cc;
}
'''

#print json.dumps(field, indent=4)



#for x in field:
#    n=field[x]["field"]
#    print "\tField(\"" + n + "\",\t" + str(field[x]["byte"]) + ",\t" + str(field[x]["bit"]) + "),"
