#!/bin/env python
#
# Field Unit Codeline Decoder Template
#
# SPCoast: John Plocher, March, 2021
#

import paho.mqtt.client as mqtt
import sys

'''
    Autogenerated MQTT Decoder
    ************************************

% for d in self.dependencyList():
    ${ '{:^34}'.format(d.name) }
% endfor

    ************************************
'''

num2node = {
% for d in self.dependencyList():
     ${ "'{:<02}'\t: '{}',".format(d.node, d.name)) }
% endfor
    '0x0069' : 'CTC'
}

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    s = "test/ctc/#"
    print("Connected with result code "+str(rc))
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe(s)
    print("Subscribed to {}".format(s))

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):

    def isSet(val, data, bit):
        v = (int(data,0) >> int(bit)) & 1
        if v:
            return val.upper()
        return val.lower() # ' - - - '

    rmax=8
    print("Topic: {}".format(msg.topic))
    if (msg.topic.lower() == 'test/ctc/spcoast/control'):
        # 10   69   00   1e  00  00  00  00  00  00  00  00  00
        (dst, src, meta, rest) = msg.payload.split(' ', 3)
        if (meta == '0x00'):
            (dst, src, meta, p0, p1, p2, p3, p4, p5, p6, p7) = msg.payload.split(' ')
            packet = [p0, p1, p2, p3, p4, p5, p6, p7, '0x00', '0x00']
            p8 = '0x00'
            p9 = '0x00'
            rmax=8
        elif (meta == '0x01' or meta == '0x0001'):
            (dst, src, meta, p0, p1, p2, p3, p4, p5, p6, p7, p8, p9) = msg.payload.split(' ')
            packet = [p0, p1, p2, p3, p4, p5, p6, p7, p8, p9]
            rmax=10
        else:
            print('Unknown codeline version: {} from {} to {}'.format(meta, src, dst))
            print('        Topic: {}  Data: {}'.format(msg.topic, msg.payload))
            sys.exit(-1)
        if dst not in num2node:
            num2node[dst]=dst
        if src not in num2node:
            num2node[src]=src
        d = {
            'ts'  : '{:<22}CONTROL         bit: +-0-----+-1-----+-2-----+-3-----++-4-----+-5-----+-6-----+-7-----+'.format(''),
            'te'  : '{:<43}+-------+-------+-------+-------++-------+-------+-------+-------+'.format(''),
            'fill': ' ',
            'topic': msg.topic,
            'payload':msg.payload,
            'pkt': map(lambda x: '{:08b}'.format(int(x, 0)), packet),
            'dst': num2node[str(dst)],
            'src': num2node[str(src)]
        }

    <%  ifstring = 'if' %>
    % for d in self.dependencyList():
        ${ '{ifstring} str(dst) == "{n}":\t# {name}\n'.format(ifstring=ifstring, n=d.node, name=d.name) }
        p = {
            'fill' : '   -',
            'dst' : num2node[str(dst)],
            'src' : num2node[str(src)],
        % for b in range(10):
        ${ "'PKT{byte}' : '{{:08b}}'.format(int(packet[{byte}], 0))[::-1],\n".format(byte=b) }
        % endfor
            <% sep = '' %>
            for _, c in d.controls.children.items():
                fname = c.name + c.suffix
                output.write("{sep}              '{f}' : isSet('{f}', packet[{byte}], {bit})".format(sep=sep, f=fname, byte=c.device, bit=c.bit))
                sep = ',\n'
            output.write('}\n')
            output.write("            print '{ts}'.format(**d)\n")
            sep = '{src:<3} => {dst:<22}'
            for device in range(d.controls.endat ):
                output.write("            print '{sep}{dev:>2}:{{PKT{dev}}}:  ".format(sep=sep, dev=device))
                sep = '                             '

                for bit in range(d.controls.bits):
                    v = d.controls.table[device][bit]
                    if (not isinstance(v, int)):
                        output.write('|{{{v}:<7}}'.format(v=v))
                    else:
                        output.write('|{{{v}:<7}}'.format(v='fill'))
                    if bit == 3:
                        output.write('|')
                output.write("|'.format(**p)\n")

            output.write("            print '{te}'.format(**d)\n")
            output.write("\n")
            ifstring = 'elif'
        % endfor


        #output.write('        else:\n')
        #output.write("            print '{src:<3} => {dst:<22} {pkt} {payload}'.format(**d)\n")
        output.write('\n')
        output.write('''
    elif (msg.topic.lower() == 'test/ctc/spcoast/indication'):
        # 69   10   00   1e  00  00  00  00  00  00  00  00  00
        (dst, src, meta, rest) = msg.payload.split(' ', 3)
        if (meta == '0x00'):
            (dst, src, meta, p0, p1, p2, p3, p4, p5, p6, p7) = msg.payload.split(' ')
            packet = [p0, p1, p2, p3, p4, p5, p6, p7, '0x00', '0x00']
            p8 = '0x00'
            p9 = '0x00'
            rmax = 8
        elif (meta == '0x01' or meta == '0x0001'):
            (dst, src, meta, p0, p1, p2, p3, p4, p5, p6, p7, p8, p9) = msg.payload.split(' ')
            packet = [p0, p1, p2, p3, p4, p5, p6, p7, p8, p9]
            rmax = 10
        else:
            print 'Unknown codeline version: {} from {} to {}'.format(meta, src, dst)
            print '        Topic: {}  Data: {}'.format(msg.topic, msg.payload)

            sys.exit(-1)
        if dst not in num2node:
            num2node[dst]=dst
        if src not in num2node:
            num2node[src]=src

        d = {
            'ts': '{:<20}INDICATION        bit: +-0-----+-1-----+-2-----+-3-----++-4-----+-5-----+-6-----+-7-----+'.format(
                ''),
            'te': '{:<43}+-------+-------+-------+-------++-------+-------+-------+-------+'.format(''),
            'fill': ' ',
            'topic': msg.topic,
            'payload': msg.payload,
            'pkt': map(lambda x: '{:08b}'.format(int(x, 0)), packet),
            'dst': num2node[str(dst)],
            'src': num2node[str(src)]
        }

''')
        ifstring = 'if'
        for d in self.dependencyList():
            output.write("        {ifstring} str(src) == '{n}':\t# {name}\n".format(ifstring=ifstring, n=d.node, name=d.name))
            output.write("            p = {\n")
            output.write("              'fill' : '   -',\n")
            output.write("              'dst' : num2node[str(dst)],\n")
            output.write("              'src' : num2node[str(src)],\n")
            for b in range(10):
                output.write("              'PKT{byte}' : '{{:08b}}'.format(int(packet[{byte}], 0))[::-1],\n".format(byte=b))

            sep = ''
            for _, c in d.indications.children.items():
                fname = c.name + c.suffix
                output.write("{sep}              '{f}' : isSet('{f}', packet[{byte}], {bit})".format(sep=sep, f=fname, byte=c.device, bit=c.bit))
                sep = ',\n'
            output.write('}\n')
            output.write("            print '{ts}'.format(**d)\n")
            sep = '{src:<22} => {dst:<3}'
            for device in range(d.indications.endat ):
                output.write("            print '{sep}{dev:>2}:{{PKT{dev}}}:  ".format(sep=sep, dev=device))
                sep = '                             '

                for bit in range(d.indications.bits):
                    v = d.indications.table[device][bit]
                    if (not isinstance(v, int)):
                        output.write('|{{{v}:<7}}'.format(v=v))
                    else:
                        output.write('|{{{v}:<7}}'.format(v='fill'))
                    if bit == 3:
                        output.write('|')
                output.write("|'.format(**p)\n")

            output.write("            print '{te}'.format(**d)\n")
            output.write("\n")
            ifstring = 'elif'

        #output.write('        else:\n')
        #output.write("            print '{src:<22} => {dst:<3} {pkt} {payload}'.format(**d)\n")
        output.write('    else:')
        output.write('        print("Data: {}".format(msg.payload))')
        output.write('\n')
        output.write('''
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("192.168.1.40", 1883, 60)

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
client.loop_forever()
''')


        output.write('\n')
        contents = output.getvalue()
        output.close()
        return contents
