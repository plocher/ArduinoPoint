## -*- coding: utf-8 -*-
//FQBN:${ cp.getFQBN() }
//PORT:${ cp.getNodeName() }
//
// Field Unit Node Template
// SPCoast: John Plocher, August, 2020
//

#include <Wire.h>
#include <elapsedMillis.h>
#include <I2Cexpander.h>
#include <MaintainerDisplay.h>
#include <SimpleHashTable.h>
#include <CodeLineMQTT.h>
#include <FieldUnit.h>

${ cp.toheading('ctc') }
${ cp.define( cp.getNodeName(), cp.getNode())}
${ cp.define('NODE_ME', cp.getNodeName()) }
% for v in cp.depends:
${ cp.define('NODE_{}'.format(v.name.upper()), v.node) }
% endfor

// event triggers for loop()
elapsedMillis displayTime;
#define DELAY_DISPLAY   (500)     // between OLED screen updates
elapsedMillis checkTime;
#define DELAY_CHECK     (100)     // between Field checks
elapsedMillis otaTime;
#define DELAY_OTA       ( 75)     // between OTA updates

${ cp.define('{}_{}'.format(cp.name.upper(), 'PORTS'), len(cp.field.children['ctc'].expanders.children))}
enum Expanders {
% for v in cp.field.children['ctc'].expanders.children:
    E${v}, // ${cp.field.children['ctc'].expanders.children[v].toString()}
% endfor
NUMEXPANDERS };

Adafruit_SSD1306 display(128, 64);   // OLED_SCREEN_WIDTH, OLED_SCREEN_HEIGHT

// ---------------------------------------------
//        Per ControlPoint identity
// ---------------------------------------------

const char *myLayoutName   = ${ '{:<20}'.format('"{}";'.format(cp.layout.lower())) }     // Many layouts can share this same MQTT topic namespace
const char* myHostname     = ${ '{:<20}'.format('"{}";'.format(cp.name)) }     // For OTA updates

// Network Configuration - these values must match your local network
const byte *myIPAddress    = NULL;                    // if NULL, use DHCP, else assign this as node's static IP address
const byte  myGW[]         = { 192,168,1,    1 };     // Gateway/router to use if not using DHCP
const byte  myNMASK[]      = { 255,255,255,  0 };     // ... and subnet mask
const char *mySSID         = "SPCoast";               // WiFi: modify to match your environment
const char *myWEP          = "railroad";              // WiFi: ...case matters!
const char *myMQTTServer   = "192.168.1.40";          // Your local mqtt server IP Address

// ---------------------------------------------

CodeLine          *codeline;
I2CMatrix         *matrix;
FieldIO           *fIO;
MaintainerDisplay *md;
FieldUnit         *fieldUnit      = NULL;
extern byte        matrix_font[128][8];

// ---------------------------------------------
//
// Controls                                     ID(byte, bit)
//
${ cp.walk(cp.controls.children)}
//
// Indications                                  ID(byte, bit)
//
${ cp.walk(cp.indications.children)}

%if len(cp.depends) > 0:
    // Dependency Indications
% for d in cp.getDependencyList():
${ cp.walk(d.indications.children)}
%endfor
%endif
//
// Field Unit                                   ID(expander, bit)
//
${ cp.walk(cp.field.children['ctc'].children) }

// ---------------------------------------------   MQTT handlers
bool handleIndications(CodeLine *cl, Indications *indication) {
    if (fieldUnit) {
        return fieldUnit->handleIndications(indication);
    }
}

bool handleControls(CodeLine *cl, Controls *control) {
    if (fieldUnit) {
        return fieldUnit->handleControls(control);
    }
}



            for d in self.dependencyList():
                output.write('/*\n')
                output.write(d.indications.totext())
                output.write('\n')
                output.write('*/\n')
                output.write(walk(d.indications.children, False))
                output.write('\n')

                output.write('/*\n')
                output.write(d.controls.totext())
                output.write('\n*/\n')
                output.write('\n')
                output.write(walk(d.controls.children, False))
                output.write('\n')

            numdepends = 0
            for d in self.dependencyList():
                output.write(define(d.name, numdepends))
                numdepends += 1

            output.write(define("NUMSTATIONS", numdepends))
            output.write('\n')

            output.write('unsigned int indications[NUMSTATIONS][NUMCODEBYTES] = {{\n'.format(numdepends))
            for d in self.dependencyList():
                output.write('    {{0,0,0,0,0,0,0,0,0,0}},\t// {}\n'.format(d.name))
            output.write('};\n')

            output.write('''
volatile boolean gotPacket = false;
I2Cexpander m[NUMPORTS];
CP controlpoints[NUMSTATIONS];
byte    yardEnter    = 6;
byte    yardExit     = 6;
byte    isEnter      = 1;

''')

            for _, CP in iter(natsorted(cp.ctcpanel.children.items())):
                if len(CP.custom) > 0:
                    output.write("extern void setup_{}(void);\n".format(CP.name))
                    output.write("extern bool loop_{}(void);\n".format(CP.name))
                    output.write(
                        "extern bool handleIndicationFor_{}(unsigned int dst, unsigned int src, unsigned int *packet);\n".format(
                            CP.name))
                    output.write("extern bool sendControlsTo_{}(void);\n".format(CP.name))

            output.write('bool handleIndications(unsigned int dst, unsigned int src, unsigned int *packet);\n')

            output.write("extern void initI2Cexpander( I2Cexpander *m );\n")

            output.write('int getNumPorts(void)          { return NUMPORTS; }\n')
            output.write('''

// receive message
void callback(char* topic, byte* payload, unsigned int length) {
    char p[length + 1];
    memcpy(p, payload, length);
    p[length] = '\\0';
    String message(p);

    unsigned int packet[NUMCODEBYTES];
    unsigned int dst, src;
    char layout[64];
    char type[64];

    cloud.decodeMQTT(topic, (const char *)payload, layout, type, &dst, &src, packet);
    char *t = strchr(layout, '/');
    if (t) {
        *t = (char)0; // split them...
        t++;
        strncpy(type, t, 20);
    }
    if (strcmp(layout, LAYOUT) == 0) { // for me...
        gotPacket = true;
        if (strcmp(type, "indication") == 0) {
            handleIndications(dst, src, packet);
        } else if (strcmp(type, "control") == 0) {
            // IGNORE for now,
            // TODO: may wish to change display if out of corospondance......
        }
    }
}

bool firsttime = true;
bool checkcodeline(void) {
    if (!client.isConnected()) {
        if (client.connect(mqtt_client_name)) {
            // Once connected, publish an announcement...
            char buf[100];
            if (firsttime) {
                sprintf(buf, "Initial connection from %s", mqtt_client_name);
                firsttime = false;
            } else {
                sprintf(buf, "Reconnect from %s", mqtt_client_name);
            }
            client.publish(mqtt_online_topic, buf );
            // ... and resubscribe
            client.subscribe(mqtt_subscription);
        } else {
            // handle backoff and retries
        }
    }
    client.loop();
    bool somethingChanged = gotPacket;
    gotPacket = false;
    return somethingChanged;
}

        ''')

            # print cp.ctcpanel.totext()
            output.write('\n')

            for _, CP in iter(natsorted(cp.ctcpanel.children.items())):
                if len(CP.custom) > 0:
                    for d in CP.custom:
                        output.write(d)
                        output.write('\n')
                # else:
                # output.write(
                #     "bool handleIndicationFor_{}(unsigned int dst, unsigned int src, unsigned int *packet) {{\n".format(
                #         CP.name))
                # for _, COL in iter(natsorted(CP.children.items())):
                #     output.write("    // Column: {} device {}\n".format(COL.name, COL.device))
                #     for _, ITEM in iter(natsorted(COL.children.items())):
                #         output.write("    //        {}: {}\n".format(ITEM.mytype, ITEM.name))
                #
                # output.write("      return false;\n")
                # output.write("}\n\n")
                # output.write("bool sendControlsTo_{}(void) {{\n".format(CP.name))
                # found = False
                # for _, COL in iter(natsorted(CP.children.items())):
                #     for _, ITEM in iter(natsorted(COL.children.items())):
                #         if (ITEM.mytype == "code") and not found:
                #             output.write("      return controlpoints[{cp}].sendControls();\n".format(cp=CP.name))
                #             found = True;
                # if not found:
                #     output.write("    return false;\n")
                # output.write("}\n")

            output.write('unsigned int name2station(const char *name) {\n')
            for _, CP in iter(natsorted(cp.ctcpanel.children.items())):
                output.write('      if (strcmp(name, "{n}") == 0)\t\treturn {n};\n'.format(n=CP.name))
            output.write('      return NUMSTATIONS;\n')
            output.write('}\n')
            output.write('\n')

            output.write('unsigned int node2station(unsigned int node) {\n')
            output.write('      switch(node) {\n')
            for _, CP in iter(natsorted(cp.ctcpanel.children.items())):
                output.write('      case NODE_{N}:\t\treturn {n};\n'.format(N=CP.name.upper(), n=CP.name))
            output.write('      default: return NUMSTATIONS;\n')
            output.write('      }\n')
            output.write('}\n')
            output.write('\n')

            output.write('// Called from async callback when new MQTT packets arrive...\n')
            output.write('bool handleIndications(unsigned int dst, unsigned int src, unsigned int *packet) {\n')
            output.write('      unsigned int s = node2station(src);\n')
            output.write('      if (s < NUMSTATIONS) {\n')
            output.write('          for (int idx = 0; idx < NUMCODEBYTES; idx++) {\n')
            output.write('              indications[s][idx] = packet[idx];\n')
            output.write('          }\n')
            output.write('      }\n')
            output.write('      switch(src) {\n')
            for _, CP in iter(natsorted(cp.ctcpanel.children.items())):
                if len(CP.custom) > 0:
                    output.write(
                        "      case NODE_{CP:<21}: return handleIndicationFor_{cp}(dst, src, packet);\n".format(
                            CP=CP.name.upper(),
                            cp=CP.name))
                else:
                    output.write(
                        "      case NODE_{CP:<26}: return controlpoints[{cp}].handleIndications(packet);\n".format(
                            CP=CP.name.upper(),
                            cp=CP.name))
            output.write('      default: return false;\n')
            output.write('      }\n')
            output.write('}\n')
            output.write('\n')

            output.write('bool sendControls(unsigned int station) {\n')
            output.write('      switch(station) {\n')
            for _, CP in iter(natsorted(cp.ctcpanel.children.items())):
                if len(CP.custom) > 0:
                    output.write("      case {cp:<26}: return sendControlsTo_{cp}();\n".format(CP=CP.name.upper(),
                                                                                               cp=CP.name))
                else:
                    output.write(
                        "      case {cp:<26}: return controlpoints[{cp}].sendControls();\n".format(CP=CP.name.upper(),
                                                                                                   cp=CP.name))

            output.write('      default: return false;\n')
            output.write('      }\n')
            output.write('}\n')
            output.write('\n')
            output.write(f.expanders.tocode())
            output.write('\n')

            output.write('void setup() {\n')
            if cp.board == 'wemos':
                output.write('      Wire.begin(D0, D1);\t// WeMos D1\n')
            else:
                output.write('      Wire.begin();\n')
            output.write('''
      initI2Cexpander(m);

      lcd.init(); delay(100);
      lcd.backlight();
      lcd.setCursor(LCD_COL_NAME, LCD_ROW_NAME);
      lcd.print(ME);

''')
            for _, CP in iter(natsorted(cp.ctcpanel.children.items())):
                if len(CP.custom) > 0:
                    output.write("        setup_{}();\n".format(CP.name))

            for _, CP in iter(natsorted(cp.ctcpanel.children.items())):
                output.write(
                    '        controlpoints[{cp:<21}].init(NODE_{CP}, {cp}, m, NUMPORTS, &cloud, &lcd)'.format(
                        CP=CP.name.upper(), cp=CP.name))
                for _, COL in iter(natsorted(CP.children.items())):
                    # output.write("    // Column: {}\n".format(COL.name))
                    for _, ITEM in iter(natsorted(COL.children.items())):
                        '''
                                General format

                                name, control packet details, ind packet details, PANEL inputs, PANEL outputs
                        '''
                        d = dict(n=ITEM.name, d=COL.device, field=cp.name, f=ITEM.cpname, col=COL.name, l=ITEM.label,
                                 pos=ITEM.position)
                        if ITEM.mytype == "code":
                            output.write('\n          ->ctc_addCODE("code",'
                                         '\n                     {field}_CODE{col}F)'.format(**d))
                        if ITEM.mytype == "call":
                            output.write('\n          ->ctc_addMC  ("{n}",'
                                         '\n                     {n}S,'
                                         '\n                     {n}K,'
                                         '\n                     {field}_{col}MCF,'
                                         '\n                     {field}_{col}MCKF)'.format(**d))
                        if ITEM.mytype == "signal":
                            output.write('\n          ->ctc_addSIG ("{n}", '
                                         '\n                     {n}SGS, {n}HS, {n}NGS,'
                                         '\n                     {n}SGK, {n}NGK, {n}TEK,'
                                         '\n                     {field}_{l}EF,  {field}_{l}SF,  {field}_{l}WF,'
                                         '\n                     {field}_{l}EKF, {field}_{l}SKF, {field}_{l}WKF)'.format(
                                **d))
                        if ITEM.mytype == "lock":
                            output.write('\n          ->ctc_addLOCK("{n}", '
                                         '\n                     {n}NWS, {n}RWS,'
                                         '\n                     {n}NWK, {n}RWK,'
                                         '\n                     {field}_{l}NF,  {field}_{l}RF,'
                                         '\n                     {field}_{l}NKF, {field}_{l}RKF)'.format(**d))
                        if ITEM.mytype == "switch":
                            output.write('\n          ->ctc_addSW  ("{n}", '
                                         '\n                     {n}NWS, {n}RWS,'
                                         '\n                     {n}NWK, {n}RWK,'
                                         '\n                     {field}_{l}NF,  {field}_{l}RF,'
                                         '\n                     {field}_{l}NKF, {field}_{l}RKF)'.format(**d))
                        if ITEM.mytype == "model":
                            output.write('\n          ->ctc_addMODEL("{n}", &indications[{f}][0],'
                                         '\n                     {n}K,'
                                         '\n                     {field}_C{col}M{pos}F)'.format(**d))
                output.write(';\n')
            output.write('}\n')
            output.write('\n')
            output.write('void loop() {\n')
            output.write('    bool somethingchanged;\n')
            for _, CP in iter(natsorted(cp.ctcpanel.children.items())):
                if len(CP.custom) > 0:
                    output.write("        somethingchanged |= loop_{}();\n".format(CP.name))
            output.write('''

    // Indication packets are handled by the callback asynchronously
    // This call manages the connection/reconnection and polling of changes (if needed)
    somethingchanged |= checkcodeline();

    for (int x = 0; x < NUMSTATIONS; x++) {
        CP::State codestate = controlpoints[x].codecheck();
        if (codestate == CP::TRIGGERED) {
            if (sendControls(x)) {
                controlpoints[x].codecheckFinish();
            }
        }
    }
}

        ''')

            output.write('\n')
            contents = output.getvalue()
            output.close()
            return contents
