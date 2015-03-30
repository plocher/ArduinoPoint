
import xml.dom.minidom
import sys
from collections import OrderedDict

__author__ = 'plocher'

def defineSW(dict, tcDict, controlpoint, DOM):
    id = DOM.getAttribute("name")
    me = {}
    me["longname"] = controlpoint + "_SW" + id
    me["name"]     = "SW" + id
    # print "defining: " + me["longname"]
    tcid= DOM.getAttribute("trackcircuit")
    me["tc"] = tcid
    me["tclongname"] = controlpoint + "_" + tcid
    _defineTC(tcDict, controlpoint, tcid)
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
    dict[id] = me

def _defineTC(dict, controlpoint, id):
    me = {}
    me["longname"]            = controlpoint + "_" + id
    me["name"]                = id
    me["indication"]          = "K" + id
    me["indicationlongname"]  = controlpoint + "_K" + id
    me["field"]               = "F" + id
    me["fieldlongname"]       = controlpoint + "_F" + id
    dict[id] = me
def defineTC(dict, controlpoint, DOM):
    id = DOM.getAttribute("name")
    _defineTC(dict, controlpoint, id)


def defineMC(dict, controlpoint, DOM):
    id = DOM.getAttribute("name")
    me = {}
    me["longname"]            = controlpoint + "_" + id
    me["name"]                =  id
    me["indication"]          = "K" + id
    me["indicationlongname"]  = controlpoint + "_K" + id
    me["field"]               = "F" + id
    me["fieldlongname"]       = controlpoint + "_F" + id
    me["control"]             = "S" + id
    me["controllongname"]     = controlpoint + "_S" + id
    # print "defining: " + me["longname"]
    dict[id] = me


def defineSIG(dict, controlpoint, DOM):
    id = DOM.getAttribute("name")
    me = {}
    me["longname"] = controlpoint + "_SIG" + id
    me["name"]     = "SIG" + id
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
    dict[id] = me


def defineIND(dict, controlpoint, DOM):
    id = "K"+DOM.getAttribute("name") #K
    me = {}
    me["longname"]            = controlpoint + "_" + id
    me["indication"]          = "" + id
    me["indicationlongname"]  = controlpoint + "_" + id
    me["byte"] = int(DOM.getAttribute("byte"))
    me["bit"]  = int(DOM.getAttribute("bit"))
    dict[id] = me

def defineCTL(dict, controlpoint, DOM):
    id = "S"+DOM.getAttribute("name") #S
    me = {}
    me["longname"]        = controlpoint + "_" + id
    me["control"]     = "S" + id
    me["controllongname"] = controlpoint + "_S" + id
    me["byte"] = int(DOM.getAttribute("byte"))
    me["bit"]  = int(DOM.getAttribute("bit"))
    dict[id] = me


def defineIO(dict, sigdict, controlpoint, DOM, io):
    id = DOM.getAttribute("name")
    if DOM.hasAttribute("byte"):
        me = {}
        me["longname"]      = controlpoint + "_F" + id
        me["field"]     = "F" + id
        me["fieldlongname"] = controlpoint + "_F" + id
        me["byte"] = int(DOM.getAttribute("byte"))
        me["bit"]  = int(DOM.getAttribute("bit"))
        me["io"]   = io
        dict[id] = me
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
            dict[h_id] = minime
            olist.append(h_id)
        for s in sigdict:
            if id in sigdict[s]["heads"]:
                #print "adding ", str(olist), " to "
                sigdict[s][id] = olist

def defineEXP(dict, controlpoint, DOM):
    me = {}
    id = "IOExpander" + DOM.getAttribute("byte") + "_" + DOM.getAttribute("type") + "_" + DOM.getAttribute("address")
    me["longname"] = controlpoint + "_" + id
    me["type"] = DOM.getAttribute("type")
    me["address"] = DOM.getAttribute("address")
    me["byte"] = int(DOM.getAttribute("byte"))
    dict[id] = me

def getText(nodelist):
    rc = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
    return ''.join(rc)

def defineCODE(dict, controlpoint, DOM):
    id = DOM.getAttribute("name")
    me = {}
    me["longname"]        = id
    me["code"]            = getText(DOM.childNodes)
    dict[id] = me


def generateDefinitions(dict, numbytes):
    a = [[0 for x in range(8)] for x in range(numbytes)]
    for k, v in dict.items():
        # print "Key: ", k, "VALUE: ", v
        byte = v["byte"]
        bit = v["bit"]
        if "io" in v:
            k = v["io"] + '_' + dict[k]["field"]
        a[byte][bit] = k
    return a


def generateExpander(dict, fieldArray, numbytes):
    a = [0 for x in range(numbytes)]  # array of expanders
    bits = [0 for x in range(numbytes)]  # array of expander initializations
    # walk thru the field bits and gather up the i/o directions for expander initialization
    for byte in range(numbytes):
        bits[byte] = ''
        empty = 1
        for bit in range(8):
            if not isinstance(fieldArray[byte][bit], int):
                empty = 0
        if not empty:
            for bit in range(8):
                v = fieldArray[byte][bit]
                if (isinstance(v, int)):
                    v = 'O_'
                if (v[1] == '_') and ((v[0] == 'I') or (v[0] == 'O')):
                    v = '0' if v[:1] == 'O' else '1'
                bits[byte] = bits[byte] + v
        if bits[byte] == '': bits[byte] = '00000000'
        # print "init[" + str(byte) + "] = " + bits[byte]
    for k, v in sorted(dict.iteritems(), key=lambda (k, v): v['byte']):
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

def read(controlpointfile):

    me = {}
    try:
        # Open XML document using minidom parser
        DOMTree = xml.dom.minidom.parse(controlpointfile)
        controlpoint = DOMTree.documentElement

        me["cpname"]     = controlpoint.getAttribute("name")
        me["layoutname"] = controlpoint.getAttribute("layout")
        me["nodenumber"] = controlpoint.getAttribute("node")
    except:
        print "Error reading or parsing control point definition: ", controlpointfile
        sys.exit(-1)

    me["sw"] = {}
    me["tc"] = {}
    me["mc"] = {}
    me["sig"] = {}
    me["ind"] = {}
    me["ctl"] = {}
    me["field"] = {}
    me["exp"] = {}
    me["code"] = {}

    me["expName"]="Ports"
    me["tcName"] ="TrackCircuits"
    me["swName"] ="Switches"
    me["mcName"] ="Calls"
    me["sigName"]="Signals"
    me["hName"]  ="Heads"

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

    for item in DOMswitches:        defineSW(  me["sw"],    me["tc"],     me["cpname"], item)
    for item in DOMtrackcircuits:   defineTC(  me["tc"],    me["cpname"], item)
    for item in DOMmaintainers:     defineMC(  me["mc"],    me["cpname"], item)
    for item in DOMsignals:         defineSIG( me["sig"],   me["cpname"], item)
    for item in DOMindications:     defineIND( me["ind"],   me["cpname"], item)
    for item in DOMcontrols:        defineCTL( me["ctl"],   me["cpname"], item)
    for item in DOMexpanders:       defineEXP( me["exp"],   me["cpname"], item)
    for item in DOMfunctions:       defineCODE(me["code"],  me["cpname"], item)
    for item in DOMinputs:          defineIO(  me["field"], me["sig"],   me["cpname"], item, "I")
    for item in DOMoutputs:
        if (not item.getAttribute("bits")):  # skip
            defineIO(me["field"], me["sig"],   me["cpname"], item, "O")

    me["field"] = OrderedDict(sorted(me["field"].items(), key=lambda (k, v): (v['byte'] * 8 + v['bit']) ))
    me["ind"]   = OrderedDict(sorted(me["ind"].items(),   key=lambda (k, v): (v['byte'] * 8 + v['bit']) ))
    me["ctl"]   = OrderedDict(sorted(me["ctl"].items(),   key=lambda (k, v): (v['byte'] * 8 + v['bit']) ))
    me["tc"]    = OrderedDict(sorted(me["tc"].items(),    key=lambda (k, v): v['longname'] ))
    me["mc"]    = OrderedDict(sorted(me["mc"].items(),    key=lambda (k, v): v['longname'] ))
    me["sw"]    = OrderedDict(sorted(me["sw"].items(),    key=lambda (k, v): v['longname'] ))
    me["sig"]   = OrderedDict(sorted(me["sig"].items(),   key=lambda (k, v): v['longname'] ))
    me["exp"]   = OrderedDict(sorted(me["exp"].items(),   key=lambda (k, v): v['longname'] ))

    me["indicationtable"] = generateDefinitions(me["ind"], 8)
    me["controltable"]    = generateDefinitions(me["ctl"], 8)
    me["fieldtable"]      = generateDefinitions(me["field"], 18)
    me["expandertable"]   = generateExpander(me["exp"], me["fieldtable"], 18)
    numheads = 0;
    for item in me["sig"]:
        numheads += len(me["sig"][item]["heads"])
    me["numheads"]=numheads
    return me
