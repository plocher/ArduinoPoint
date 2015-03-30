import sys
import StringIO

__author__ = 'plocher'

def table(table, tablename, cpname, numbytes):
    output = StringIO.StringIO()
    output.write(' *        ' + tablename + ' for ' + cpname + '\n')
    output.write(' *        +---------+---------+---------+---------+---------+---------+---------+---------+\n')
    prepend = ' *        | '
    for bit in range(8):
        output.write(prepend)
        prepend = '| '
        v = 'bit ' + str(bit)
        output.write(v)
        for filler in range(len(v), 8):
            output.write(' ')
    output.write('|\n')
    output.write(' *        +---------+---------+---------+---------+---------+---------+---------+---------+\n')
    for byte in range(numbytes):
        empty = 1
        for bit in range(8):
            if not isinstance(table[byte][bit], int):
                empty = 0
        if not empty:
            output.write(' * Byte ' + str(byte) + ' | ')
            prepend = ''
            for bit in range(8):
                output.write(prepend)
                prepend = '| '
                v = table[byte][bit]
                if (isinstance(v, int)):
                    v = '- - - -'
                if (len(v) >2) and (v[1] == '_') and ((v[0] == 'I') or (v[0] == 'O')):
                    v = v[:1].lower() + ' ' + v[2:]
                output.write(v)
                for filler in range(len(v), 8):
                    output.write(' ')
            output.write('|\n')
    output.write(' *        +---------+---------+---------+---------+---------+---------+---------+---------+')
    contents = output.getvalue()
    output.close()
    return contents


def expander(table, tablename, cpname, numbytes):
    output = StringIO.StringIO()
    output.write(' *        ' + tablename + ' for ' + cpname + '\n')
    output.write(' *        +-------------------------------------------------------------------------------+\n')
    for byte in range(numbytes):
        me = table[byte]
        if me:
            output.write(' * Byte ' + str(byte) + ' | ')
            output.write(
                me["type"] + "\tChip Address: " + me["address"] + "\tI/O Map: B" + me["init"] + "\t(1=input, 0=output)\t  |\n")
    output.write(' *        +-------------------------------------------------------------------------------+')
    contents = output.getvalue()
    output.close()
    return contents

def boxed_text(pre, s, c, overhang):
    output = StringIO.StringIO()
    l = len(s)
    output.write(pre)
    for filler in range(l + overhang * 2):
        output.write(c)
    output.write('\n')
    output.write(pre)
    for filler in range(overhang):
        output.write(' ')
    output.write(s + '\n')
    output.write(pre)
    for filler in range(l + overhang * 2):
        output.write(c)
    #output.write('\n')
    contents = output.getvalue()
    output.close()
    return contents

def include(file):
    return "#include <" + file + ">"

def M(cpname, name):
    return "{c}_{n}".format(c=cpname.upper(),n=name)

def M_Appliance(cpname, name):
    return "{c}_Num{n}".format(c=cpname, n=name)

def NUMDefine(cpname, name, size):
    return ("#define {M}\t{s}\n")                        .format(M=M_Appliance(cpname, name), s=size)
def NUMFunction(cpname, name, size):
    return ("int getNum{n}(void)\t{{ return ({M}); }}\n").format(M=M_Appliance(cpname, name), n=name)

# #define CP_Christopher_NumPorts	6
def numDefines(me):
    return (
          NUMDefine(me["cpname"], me["expName"],   len(me["exp"]))
        + NUMDefine(me["cpname"], me["tcName"],    len(me["tc"]))
        + NUMDefine(me["cpname"], me["swName"],    len(me["sw"]))
        + NUMDefine(me["cpname"], me["mcName"],    len(me["mc"]))
        + NUMDefine(me["cpname"], me["sigName"],   len(me["sig"]))
        + NUMDefine(me["cpname"], me["hName"],     me["numheads"])
    )

# int getNumCP_Christopher(void)	{ return (CP_Christopher_NumPorts); }
def numFunctions(me):
    return (
          NUMFunction(me["cpname"], me["expName"], len(me["exp"]))
        + NUMFunction(me["cpname"], me["tcName"],  len(me["tc"]))
        + NUMFunction(me["cpname"], me["swName"],  len(me["sw"]))
        + NUMFunction(me["cpname"], me["mcName"],  len(me["mc"]))
        + NUMFunction(me["cpname"], me["sigName"], len(me["sig"]))
        + NUMFunction(me["cpname"], me["hName"],   me["numheads"])
    )

def applianceDefines(dict):
    output = StringIO.StringIO()
    counter = 0
    for item in dict:
        output.write("#define "+str(dict[item]["longname"])+"\t" + str(counter) + '\n')
        counter += 1
    contents = output.getvalue()
    output.close()
    return contents

def codelineDefines(dict):
    output = StringIO.StringIO()
    for item in dict:
        output.write("#define "+str(dict[item]["longname"])+"\t" +
                     str(int(dict[item]["byte"]) * 8 + int(dict[item]["bit"])) + '\n')
    contents = output.getvalue()
    output.close()
    return contents
