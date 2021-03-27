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

${ cp.toheading('fieldunit') }
#define NODE_CTC                                0x0069
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

${ cp.define('{}_{}'.format(cp.name.upper(), 'PORTS'), len(cp.field.children['fieldunit'].expanders.children))}
enum Expanders {
% for v in cp.field.children['fieldunit'].expanders.children:
    E${v}, // ${cp.field.children['fieldunit'].expanders.children[v].toString()}
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
${ cp.walk(cp.field.children['fieldunit'].children) }

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


void setup(void) {
    unsigned long int startmem = ESP.getFreeHeap(), finishmem;

    Serial.begin(115200);
    while (!Serial) {
      ; // wait for serial port to connect. Needed for Native USB
    }

    Serial.print("ControlPoint Firmware: ");
    Serial.print(myLayoutName);
    Serial.print(":");
    Serial.print(myHostname);
    if (myIPAddress) {
        Serial.print(" (");
        Serial.print(myIPAddress[0]);Serial.print(".");
        Serial.print(myIPAddress[1]);Serial.print(".");
        Serial.print(myIPAddress[2]);Serial.print(".");
        Serial.print(myIPAddress[3]);Serial.print(") ");
    }
    Serial.print(" Node 0x"); Serial.println(NODE_ME, HEX);
    Wire.begin(21,22);  // for ESP32-DEV

    matrix   = new I2CMatrix(0x01, 2);
    md       = new MaintainerDisplay();
    md->init(&display);

    codeline = new CodeLine(myHostname, myLayoutName,  myMQTTServer, mySSID, myWEP, myGW, myNMASK, NODE_ME, md, matrix, myIPAddress);
    codeline->update(MaintainerDisplay::REFRESH);    // update OLED with codeline state for debugging
    codeline->registerCHandler(handleControls);
    codeline->registerIHandler(handleIndications);
    <% expanderlist=cp.field.children['fieldunit'].expanders.children %>

    // Field I/O abstraction - collection of all appliances in Field Unit
    fIO      = new FieldIO(NUMEXPANDERS);
    //        #   addr  type                   group 4           group 3           group 2           group 1
    % for v in expanderlist:
    fIO->init(E${v}, ${expanderlist[v].addr}, I2Cexpander::${expanderlist[v].type}, ${expanderlist[v].typedinit});
    % endfor

    // Field Unit abstraction - all the subsystems used by the Field Unit
    fieldUnit = new FieldUnit(myHostname, myLayoutName, ${ cp.getNodeName() }, NODE_CTC, fIO, codeline);

    // Maintainer Call
    % for k, v in cp.getMaintainerCallList():
    // ${v.doc}
    fieldUnit->add(new MaintainerCallDevice(${'{qualname:<30} {n:<25} {c:<25} {i:<25} {f:<25}'.format(
                                                qualname='"{cpname}:{id}",'.format(cpname=cp.name, id=k),
                                                n='{},'.format(v.nodeName()),
                                                c='{},'.format(v.Name(False, True)),
                                                i='{},'.format(v.Name(True, false)),
                                                f=v.Name()) } ));
    % endfor

    // Track Power

    % for k, v in cp.getTrackPowerList():
    // ${v.doc}
    // fieldUnit->add(new TrackPowerDevice(${'{qualname:<30} {n:<25}'.format(qualname='"{cpname}:{id}",'.format(cpname=cp.name, id=k), n='{},'.format(v.nodeName()))  }
    //     /* controls       */             ${v.prefix('PONS') },       ${v.prefix('POFFS') },
    //     /* indications    */             ${v.prefix('SHORT') },      ${v.prefix('TONK') },    ${v.prefix('OCCK') },   ${v.prefix('OFFK') },
    //     /* Track Circuit  */             ${v.prefix('SHORTF') },     ${v.prefix('TONF') },    ${v.prefix('OCCF') },   ${v.prefix('OFFF') });

    % endfor
    // Track Circuits
    % for k, v in cp.getTrackCircuitList():
    fieldUnit->add(new TrackCircuitDevice(  ${'{qualname:<30} {n:<25} {i:<25} {f:<25}'.format(
                                              qualname='"{cpname}:{id}",'.format(cpname=cp.name, id=k),
                                              n='{},'.format(v.nodeName()),
                                              c='{},'.format(v.Name(False, True)),
                                              i='{},'.format(v.Name(True, false)),
                                              f=v.Name() )} ));
    % endfor

    // Sections
    % for k, v in cp.getSectionList():
    // ${v.doc}
    SectionDevice *d = new SectionDevice(   ${'{qualname:<30} {n:<25} {i:<25}'.format(
                                              qualname='"{cpname}:{id}",'.format(cpname=cp.name, id=k),
                                              n='{},'.format(v.nodeName()),
                                              i='{}'.format(v.Name(True, false)),
                                              f=v.Name() )} ));
    % for tcname, tc in v.TCs.items():
        d->add((TrackCircuitDevice*)fieldUnit->get( "${cp.name}:${tcname}" ));
    %endfor
    fieldUnit->add(d);

    % endfor
    // Switches
    % for k, v in cp.getSwitchList():
    fieldUnit->add(new SwitchDevice("${cp.name}:${ k }", ${ v.nodeName() },
        /* Track Circuit  */   (TrackCircuitDevice *)fieldUnit->get("${v.tc}"),
        /* controls       */   ${ v.cN() }, ${ v.cR() },
        /* indications    */   ${ v.iN() }, ${ v.iR() },
        /* fieldunit      */   ${ v.fM() }, ${ v.fN() }, ${ v.fR() }));
    % endfor

    // Signals
    % for sk, sv in cp.getSigList():
    fieldUnit->add(new SignalDevice("${cp.name}:${ sk }", ${ cp.getNodeName() },
        /* controls        */  ${ sv.cLeft() }, ${ sv.cRight() }, ${ sv.cSTOP() },      // L, R, Stop
        /* indications     */  ${ sv.iLeft() }, ${ sv.iRight() }, ${ sv.iTimer() }));   // L, R, TimeElement
    % endfor

    SignalDevice *s = NULL;
    SignalHead *h = NULL;
    % for fk, fv in cp.field.children.items():
        % if fk == 'fieldunit':
            % for smname, sm in fv.signals.children.items():
                <% signalFullName = '{cpname}:{smname}'.format(cpname=cp.name, smname=smname) %>
                <% siga = sm.sig %>
                <% docstring = siga.doc %>
                % if docstring is None:
                    <% docstring = '' %>
                % endif
            // ===================================================================
            // ${cp.name} Signal ${smname}: ${docstring}
            // ===================================================================

            s = (SignalDevice *)fieldUnit->get("${signalFullName}");

                % if (siga.fleet is not None) and (siga.er is not None):
                    %if (siga.fleet.lower() == 'true') and (siga.er.lower() == 'true'):
            s->setStick(SignalDevice::FLEET_ER);
                    %elif (siga.fleet.lower() == 'true') and (siga.er.lower() != 'true'):
            s->setStick(SignalDevice::FLEET);
                    %elif (siga.fleet.lower() == 'true') and (siga.er.lower() != 'true'):
            s->setStick(SignalDevice::ER);
                    %endif
                %endif

                % for shname, sh in sm.children.items():
                    <% mastFullName = '{cpname}:{shname}'.format(cpname=cp.name, shname=shname) %>
                    <% heada = siga.getMast(mastFullName) %>
                    <% docstring = heada.doc %>
                    %if docstring is None:
                        <% docstring = '' %>
                    %endif
                // --------------------------------------------------------------
                // ${mastFullName} ${docstring}
                // --------------------------------------------------------------
                //
                    <% s='' %>
                    <% sep='' %>
                    <% l=sh.field.children.items() %>
                    % if l:
                        <% l=cp.order( l ) %>
                    % endif
                    % for outname, out in l:
                        <% s = s + sep + cp.name + '_' + outname + 'F' %>
                        <% sep = ', ' %>
                    %endfor
                h = new SignalHead_${sh.type}("${mastFullName}", ${s} );
                s->addHead(h);

                    % for rk, rv in heada.route.children.items():
                        <% docstring = rv.doc %>
                        % if docstring is None:
                            <% docstring = ''  %>
                        %endif

                    // --------------------------------------------------------------
                    // Route "${rk}" ${docstring}
                    // --------------------------------------------------------------
                        % if rv.default_aspect is None:
                    // No default aspect provided
                            % for val, item in rv.children.items():
                                <% s='{routename:<15} {condition}'.format(routename='"{key}",'.format(key=rk), condition=item.toSignalCode(True)) %>
                    h->addRouteDependency(${s})
                            % endfor
                        %else:
                            <% s='{routename:<15} {aspect}'.format(routename='"{key}",'.format(key=rk), aspect=rv.default_aspect) %>
                    h->createRoute(${s});
                            % for val, item in rv.children.items():
                                <% s='{routename:<15} {condition}'.format(routename='"{key}",'.format(key=rk), condition=item.toSignalCode(False)) %>
                    h->addRouteDependency(${s});
                            % endfor
                        % endif
                    %endfor

                %endfor
            %endfor
        %endif
    %endfor

    finishmem = ESP.getFreeHeap();
    Serial.print("Heap memory used: ");
    Serial.print((startmem - finishmem) / 1024);
    Serial.print("k, available: ");
    Serial.print(finishmem / 1024);
    Serial.println("k");
}

void loop(void) {
    bool somethingchanged = false;

    if (otaTime > DELAY_OTA) {                              // Check connection to WiFi/MQTT/OTA Firmware updates
        somethingchanged = codeline->CheckCodeLine();
        otaTime = 0;
    }

    if (displayTime > DELAY_DISPLAY) {                      // Update the display
        displayTime = 0;
        codeline->update(MaintainerDisplay::REFRESH);
    }

    if (somethingchanged || (checkTime > DELAY_CHECK)) {    // check the field appliances and process changes
        fieldUnit->run(somethingchanged);
        checkTime = 0;
    }
}

