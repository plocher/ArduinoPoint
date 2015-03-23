#!/usr/bin/python

import xml.dom.minidom
import sys
from collections import OrderedDict
import json


def defineSW(sw, tc, controlpoint, DOM):
    id = DOM.getAttribute("name")
    me = {}
    me["longname"] = controlpoint + "_SW" + id
    # print "defining: " + me["longname"]
    tcid= DOM.getAttribute("trackcircuit")
    me["tc"] = tcid
    me["tclongname"] = controlpoint + "_" + tcid
    _defineTC(tc, controlpoint, tcid)
    i = {}
    i["normal"]          = "K" + id + "NW"
    i["reverse"]         = "K" + id + "RW"
    i["normallongname"]  = controlpoint + "_K" + id + "NW"
    i["reverselongname"] = controlpoint + "_K" + id + "RW"
    me["indication"]     = i
    c = {}
    c["normal"]          = "S" + id + "NW"
    c["reverse"]         = "S" + id + "RW"
    c["normallongname"]  = controlpoint + "_S" + id + "NW"
    c["reverselongname"] = controlpoint + "_S" + id + "RW"
    me["control"]        = c
    f = {}
    f["normal"]          =  ""   + id  + "NW"
    f["reverse"]         =  ""   + id  + "RW"
    f["motor"]           =  "T"  + id
    f["normalname"]      =  "F"  + id  + "NW"
    f["reversename"]     =  "F"  + id  + "RW"
    f["motorname"]       =  "FT" + id
    f["normallongname"]  =  controlpoint + "_F"  + id  + "NW"
    f["reverselongname"] =  controlpoint + "_F"  + id  + "RW"
    f["motorlongname"]   =  controlpoint + "_FT" + id
    me["field"] = f
    sw[id] = me

def _defineTC(tc, controlpoint, id):
    me = {}
    me["longname"]            = controlpoint + "_" + id
    me["indication"]          = "K" + id
    me["indicationlongname"]  = controlpoint + "_K" + id
    me["field"]               = "F" + id
    me["fieldlongname"]       = controlpoint + "_F" + id
    tc[id] = me
def defineTC(tc, controlpoint, DOM):
    id = DOM.getAttribute("name")
    _defineTC(tc, controlpoint, id)


def defineMC(mc, controlpoint, DOM):
    id = DOM.getAttribute("name")
    me = {}
    me["longname"]            = controlpoint + "_" + id
    me["indication"]          = "K" + id
    me["indicationlongname"]  = controlpoint + "_K" + id
    me["field"]               = "F" + id
    me["fieldlongname"]       = controlpoint + "_F" + id
    me["control"]             = "S" + id
    me["controllongname"]     = controlpoint + "_S" + id
    # print "defining: " + me["longname"]
    mc[id] = me


def defineSIG(sig, controlpoint, DOM):
    id = DOM.getAttribute("name")
    me = {}
    me["longname"] = controlpoint + "_SIG" + id
    #print "defining: " + me["longname"] + " from id=|"+id+"|"
    i = {}
    i["north"]     = "K" + id + "NG"
    i["south"]     = "K" + id + "SG"
    i["northlongname"] = controlpoint + "_K" + id + "NG"
    i["southlongname"] = controlpoint + "_K" + id + "SG"
    me["indication"] = i
    c = {}
    c["north"]     = "S" + id + "NG"
    c["south"]     = "S" + id + "SG"
    c["stop"]      = "S" + id + "H"
    c["northlongname"] = controlpoint + "_S" + id + "NG"
    c["southlongname"] = controlpoint + "_S" + id + "SG"
    c["stoplongname"]  = controlpoint + "_S" + id + "H"
    me["control"] = c
    heads = []
    DOMheads = DOM.getElementsByTagName("head")
    for h in DOMheads:
        hn=h.getAttribute("name")
        heads.append(hn)
        me[hn+"longname"] = controlpoint + "_" + hn
    me["heads"] = heads
    sig[id] = me


def defineIND(ind, controlpoint, DOM):
    id = "K"+DOM.getAttribute("name") #K
    me = {}
    me["longname"]            = controlpoint + "_" + id
    me["indication"]          = "" + id
    me["indicationlongname"]  = controlpoint + "_" + id
    me["byte"] = int(DOM.getAttribute("byte"))
    me["bit"]  = int(DOM.getAttribute("bit"))
    ind[id] = me

def defineCTL(ctl, controlpoint, DOM):
    id = "S"+DOM.getAttribute("name") #S
    me = {}
    me["longname"]        = controlpoint + "_" + id
    me["control"]     = "S" + id
    me["controllongname"] = controlpoint + "_S" + id
    me["byte"] = int(DOM.getAttribute("byte"))
    me["bit"]  = int(DOM.getAttribute("bit"))
    ctl[id] = me


def defineIO(field, controlpoint, DOM, io):
    global sig
    id = DOM.getAttribute("name")
    if DOM.hasAttribute("byte"):
        me = {}
        me["longname"]      = controlpoint + "_F" + id
        me["field"]     = "F" + id
        me["fieldlongname"] = controlpoint + "_F" + id
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
            minime["longname"] = controlpoint + "_" + h_id
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
    me["longname"] = controlpoint + "_" + id
    me["type"] = DOM.getAttribute("type")
    me["address"] = DOM.getAttribute("address")
    me["byte"] = int(DOM.getAttribute("byte"))
    exp[id] = me

def getText(nodelist):
    rc = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
    return ''.join(rc)

def defineCODE(code, controlpoint, DOM):
    id = DOM.getAttribute("name")
    me = {}
    me["longname"]        = id
    me["code"]            = getText(DOM.childNodes)
    code[id] = me


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
        me["longname"] = "IOexpander_" + str(byte)
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
                if (len(v) >2) and (v[1] == '_') and ((v[0] == 'I') or (v[0] == 'O')):
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
    global sw, tc, mc, sig, ind, ctl, field, exp, code
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
    DOMswitches      = controlpoint.getElementsByTagName("switch")
    DOMtrackcircuits = controlpoint.getElementsByTagName("trackcircuit")
    DOMmaintainers   = controlpoint.getElementsByTagName("call")
    DOMsignals       = controlpoint.getElementsByTagName("signal")
    DOMindications   = controlpoint.getElementsByTagName("indication")
    DOMcontrols      = controlpoint.getElementsByTagName("control")
    DOMinputs        = controlpoint.getElementsByTagName("input")
    DOMoutputs       = controlpoint.getElementsByTagName("output")
    DOMexpanders     = controlpoint.getElementsByTagName("expander")
    DOMfunctions     = controlpoint.getElementsByTagName("function")

    for item in DOMswitches:
        defineSW(sw, tc, cpname, item)
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
    for item in DOMfunctions:
        defineCODE(code, cpname, item)

    field = OrderedDict(sorted(field.items(), key=lambda (k, v): (v['byte'] * 8 + v['bit']) ))
    ind   = OrderedDict(sorted(ind.items(),   key=lambda (k, v): (v['byte'] * 8 + v['bit']) ))
    ctl   = OrderedDict(sorted(ctl.items(),   key=lambda (k, v): (v['byte'] * 8 + v['bit']) ))
    tc    = OrderedDict(sorted(tc.items(),    key=lambda (k, v): v['longname'] ))
    mc    = OrderedDict(sorted(mc.items(),    key=lambda (k, v): v['longname'] ))
    sw    = OrderedDict(sorted(sw.items(),    key=lambda (k, v): v['longname'] ))
    sig   = OrderedDict(sorted(sig.items(),   key=lambda (k, v): v['longname'] ))
    exp   = OrderedDict(sorted(exp.items(),   key=lambda (k, v): v['longname'] ))

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
code = {}
expName="Ports"
tcName ="TrackCircuits"
swName ="Switches"
mcName ="Calls"
sigName="Signals"
hName  ="Heads"


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
printInclude("I2Cextender.h")
printInclude("elapsedMillis.h")
printInclude("ControlPoint.h")

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

if ("common" in code):
    print code["common"]["code"]
else :
    print "// No user defines found"
print ""
print "int determineAspect(int signalHead);             // User defined"
print "int knockdownSignal(int signalName);             // User defined"
print "void debugCallBack(boolean somethingchanged);    // User defined"
print ""

numheads = 0;
for item in sig:
    numheads += len(sig[item]["heads"])

NUMfmt="{c}_Num{n}"
def printNUMDefines(cpname, name, size):
    print ("#define "+NUMfmt+"\t{s}")                        .format(c=cpname, n=name, s=size)
def printNUMFunctions(cpname, name, size):
    print ("int getNum{n}(void)\t{{ return ("+NUMfmt+"); }}").format(c=cpname, n=name, s=size)
def printNums(type):
    if (type == 'defines'):
        printNUMDefines(cpname, expName,   len(exp))
        printNUMDefines(cpname, tcName,    len(tc))
        printNUMDefines(cpname, swName,    len(sw))
        printNUMDefines(cpname, mcName,    len(mc))
        printNUMDefines(cpname, sigName,   len(sig))
        printNUMDefines(cpname, hName,     numheads)
    else:
        printNUMFunctions(cpname, expName, len(exp))
        printNUMFunctions(cpname, tcName,  len(tc))
        printNUMFunctions(cpname, swName,  len(sw))
        printNUMFunctions(cpname, mcName,  len(mc))
        printNUMFunctions(cpname, sigName, len(sig))
        printNUMFunctions(cpname, hName,   numheads)

printNums("defines")
print ""
printNums("functions")
print ""
print "#ifdef HASLCD"
print "#include <LiquidTWI.h>"
print "LiquidTWI lcd(7);  // Set the LCD I2C address"
print "#endif"
print "boolean localcontrol = true;  // need to add support for local-vs-dispatcher control, till then, punt"

print ""
print "I2Cextender m[" + M("PORTS") + "];"
print ""

def printApplianceDefines(dict):
    counter = 0
    for item in dict:
        print "#define " + str(dict[item]["longname"]) + "\t" + str(counter)
        counter += 1
def printCodelineDefines(dict):
    for item in dict:
        print "#define " + str(dict[item]["longname"]) + "\t" + str(int(dict[item]["byte"]) * 8 + int(dict[item]["bit"]))

print "// Appliances (TrackCircuits, Switches, Maintainers, Signals and Heads)"
printApplianceDefines(tc)
printApplianceDefines(sw)
printApplianceDefines(mc)
printApplianceDefines(sig)
counter=0
for item in sig:
    headlist=sig[item]["heads"]
    for head in headlist:
        print "#define "+ sig[item][str(head)+"longname"] + "\t" + str(counter)
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
print ("TrackCircuit track[" + NUMfmt + "] = {{").format(c=cpname, n=tcName)
for item in tc:
    s="\tTrackCircuit(\"{i}\",\t&m[toByte({f})],\ttoBit({f}))," +"\t\t\t// {n}"
    print s.format(i=item,
                   f=str(tc[item]["fieldlongname"]),
                   n=str(tc[item]["longname"]))
print "};"

print ("Switch sw[" + NUMfmt + "] = {{").format(c=cpname, n=swName)
for item in sw:
    f=sw[item]["field"]
    s="\tSwitch(\"{i}\",\t\t&m[toByte({n})],\ttoBit({n}),\t toBit({r}),\t toBit({m})),\t// {l}"
    print s.format(i=item,
                   n=str(f["normallongname"]),
                   r=str(f["reverselongname"]),
                   m=str(f["motorlongname"]),
                   l=str(sw[item]["longname"]))
print "};"

print ("Maintainer mc[" + NUMfmt + "] = {{").format(c=cpname, n=mcName)
for item in mc:
    s="\tMaintainer(\"{i}\",\t&m[toByte({f})],\ttoBit({f})),\t\t\t// {n}"
    print s.format(i=item,
                   f=str(mc[item]["fieldlongname"]),
                   n=str(mc[item]["longname"]))
print "};"

print ("RRSignal sig[" + NUMfmt + "] = {{").format(c=cpname, n=sigName)
for item in sig:
    s="\tRRSignal(\"{i}\"),\t\t\t\t\t\t// {l}"
    print s.format(i=item ,
                   l=str(sig[item]["longname"]))
print "};"

print ("RRSignalHead head[" + NUMfmt + "] = {{").format(c=cpname, n=hName)
for item in sig:
    headlist=sig[item]["heads"]
    for head in headlist:
        sys.stdout.write("\tRRSignalHead(\"{}\",\t".format(head ))
        headfields = sig[item][head]
        pre=0
        for hf in headfields :
            if not pre :
                sys.stdout.write("&m[{}]".format(str(field[hf]["byte"])))
                pre=",\t"
            sys.stdout.write(pre + str(field[hf]["bit"]))
        print ")," + "\t\t// "+ sig[item][str(head)+"longname"]
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

if ("determineAspect" in code):
    print code["determineAspect"]["code"]
else :
    print "int determineAspect(int signalHead) { return RRSignalHead::STOP; }   // Routine not found in CP definition"
if ("knockdownSignal" in code):
    print code["knockdownSignal"]["code"]
else :
    print "int knockdownSignal(int signalName) { return 0; }                    // Routine not found in CP definition"

print '''
boolean processSignals() {
        boolean somethingchanged = false;
        for (int x = 0; x < getNumSignals(); x++) {
            if (sig[x].runTime() == RRSignal::EXPIRED) {
                sig[x].report();
                somethingchanged = true;
            }
        }
        // knock down signals ...
'''
for item in sig:
    name=str(sig[item]["longname"])
    print "\tsomethingchanged |= knockdownSignal(" + name + ");"
print ""
for item in sig:
    headlist=sig[item]["heads"]
    for head in headlist:
        name = sig[item][str(head)+"longname"]
        sys.stdout.write("\thead[" + name + "].set((RRSignalHead::Aspects)determineAspect("+ name +"));\n")
print '''
        return somethingchanged;
}

boolean handleControlPacket(int src, int dst, int *controls, boolean force) {
        boolean cc = false;
        int safe = true;

        if (src == NODE_ME) {                           // I sent this one...
                  // Serial.println(" (Ignoring my loopback Indication Packet...)");
        } else if ((src != NODE_CTC) && (src != NODE_LOCAL)) {                   // Don't pay attention to gossip :-)
                  // Serial.println(" (Ignoring other unit's Indication Packet...)");
        } else if (dst != NODE_ME) {           // for someone else...
                  // Serial.println(" (Ignoring other unit's Control Packet...)");
        } else {                                        // for me!
                int idxN, offN;
                int idxS, offS;
                cc = true;

                // Is this a safe command?
'''
print "\t\t//   Plant must be empty (switches not fouled...)"
for item in sw:
    print "\t\tsafe &= !track[" + str(sw[item]["tclongname"]) + "].is(TrackCircuit::OCCUPIED);"
print ""
print "\t\t//   Control packet must make sense"
for item in sw:
    swname=str(sw[item]["longname"])
    swNname=sw[item]["control"]["normallongname"]
    swRname=sw[item]["control"]["reverselongname"]
    print "\t\tsafe &= sw["+swname+"]\t.isSafe(&controls[toByte("+swNname+")], toBit("+swNname+"), toBit("+swRname+ ") );"
print ""
for item in sig:
    signame=str(sig[item]["longname"])
    sigSTOPname=str(sig[item]["control"]["stoplongname"])
    sigNname=str(sig[item]["control"]["northlongname"])
    sigSname=str(sig[item]["control"]["southlongname"])
    print "\t\tsafe &= sig["+signame+"].isSafe("
    print "\t\t\tbitRead(controls[toByte(" +sigSname+")], toBit("  +sigSname+")), "
    print "\t\t\tbitRead(controls[toByte(" +sigNname+")], toBit("  +sigNname+")) );"
print ""
print "\t\t// can only change FLEET stick and MC lights while plant is occupied"

if len(mc):
    for item in mc:
        f=str(mc[item]["field"])
        mcname=str(mc[item]["longname"])
        mcCname=str(mc[item]["controllongname"])
        print "\t\tmc["+mcname+"].set(bitRead(controls[toByte("+mcCname+")], toBit("+mcCname+")));"
    print "\t}"

else:
    print "\t\t// There is no MC defined for this CP"
print '''
        // TODO: Need to deal with fleet controls
        if (force) safe=1;  // At startup, force the CP to initialize into the last saved state
        if (!safe) {
#ifdef DEBUG
            Serial.println("VITAL level plant reject");
#endif
#ifdef HASLCD
            lcd.setCursor(17,  0); lcd.print("VR");
#endif
        } else {  // valid control packet...
#ifdef HASLCD
            lcd.setCursor(17,  0); lcd.print("OK");
#endif
            for (int x = 0; x <  getNumSwitches(); x++) {
                sw[x].doSafe();
            }
            for (int x = 0; x <   getNumSignals(); x++) {
                sig[x].doSafe();
            }
            ControlPoint::savestate(controls);  // remember last commanded turnout state in eeprom...
        }
        return cc;
}

void collectAndSendIndications(void) {
        int indications[8];

        for (int x = 0; x < 8; x++) {
            indications[x] = B00000000;
        }
        // Switches'''
for item in sw:
    name  =sw[item]["longname"]
    iNname=sw[item]["indication"]["normallongname"]
    iRname=sw[item]["indication"]["reverselongname"]
    print "\tbitWrite(indications[toByte("+iNname+")], toBit("+iNname+"), sw["+name+"].is(Switch::NORMAL));"
    print "\tbitWrite(indications[toByte("+iRname+")], toBit("+iRname+"), sw["+name+"].is(Switch::REVERSE));"

print "\t// Track Circuits"
for item in tc:
    name  = tc[item]["longname"]
    iname = tc[item]["indicationlongname"]
    print "\tbitWrite(indications[toByte("+iname+")], toBit("+iname+"), track["+name+"].is(TrackCircuit::OCCUPIED));"

print "\t// Signals"
for item in sig:
    name    = sig[item]["longname"]
    iNname  = sig[item]["indication"]["northlongname"]
    iSname  = sig[item]["indication"]["southlongname"]
    print "\tbitWrite(indications[toByte("+iSname+")], toBit("+iSname+"), sig["+name+"].leftindication());\t// SIGNALS"
    print "\tbitWrite(indications[toByte("+iNname+")], toBit("+iNname+"), sig["+name+"].rightindication());\t// AT STOP?"

print '''
    (void)ControlPoint::sendCodeLine(NODE_ME, NODE_CTC, indications);
}

#ifdef HASLCD
void lcdprintbin(byte x) {
    char buff[8+1];
    for (int i = 0; i < 8; i++) {
	buff[i] = (bitRead(x,i) ? '1' : '0');
    }
    buff[8] = '\0';
    lcd.print(buff);
}
#endif

'''
if ("debugCallback" in code):
    print code["debugCallback"]["code"]
else :
    print "void debugCallBack(boolean somethingchanged) { return; }     // Routine not found in CP definition"

print '''
// boilerplate 'duino routines; CP specifics are encapsulated in common code in ControlPoint::setup and ControlPoint::loop

void setup(void)
{
#ifdef DEBUG
    // Configure the serial port
    Serial.begin(115200);    while (!Serial);
    Serial.println(ME);
    Serial.print("Free RAM: "); Serial.print(ControlPoint::freeRam(), DEC); Serial.println("");
#endif
#ifdef HASLCD
    lcd.begin(20,4);               // initialize the lcd
    lcd.setBacklight(HIGH);
    lcd.home();
    lcd.print(ME);
#endif
    ControlPoint::initializeCodeLine(LNET_RX_PIN,LNET_TX_PIN);
    Wire.begin();
    initI2Cextender(m);
    ControlPoint::setup();
'''
print "\t// Set all Signals to allow local panel overrides for now"
for item in sig:
    name    = sig[item]["longname"]
    iNname  = sig[item]["indication"]["northlongname"]
    iSname  = sig[item]["indication"]["southlongname"]
    print "\tsig["+name+"].local(true);  // when plant is occupied, show STOP (false) or RESTRICTING (true) ?"
print '''
}

int controls[8];
int src, dst;

void loop(void) {
    boolean somethingChanged = false;
    somethingChanged = ControlPoint::readall();
    int cc = ControlPoint::LnPacket2Controls(&src, &dst, controls);                       // 0 = no packet
    if (cc == 1) { somethingChanged |= handleControlPacket(src, dst, controls, false); }  // 1 = routine use, checkplant safety
    if (cc == 2) { somethingChanged |= handleControlPacket(src, dst, controls, true ); }  // 2 = startup with old configuration
    somethingChanged |= processSignals();

    if (somethingChanged) {
        collectAndSendIndications();
    }
    debugCallBack(somethingChanged);
    ControlPoint::writeall();
}

'''
