# ArduinoPoint
Generate Arduino Sketch for a Model Railroad Control Point from an XML template

# UI Thoughts

## Workflow

  * Mindset:  you are editing a control point field unit that hosts a set of field appliances and communicates through a codeline.
  * Appliances include things like Switches, Signals, Track Circuits, Maintainer Call lights, Sensors and Actuators
  * The CodeLine protocol involves Control packets sent TO, and Indication Packets sent FROM a field unit

  1. Start with blank control point node
  2. Set properties: Name, Address...
  3. Create/Modify a text, sprite or graphic based track schematic of the Control Point using a pallet of Appliances:  
     * Track Sections with Track Circuit Detectors
     * Track Sections without Track Circuit Detectors
     * Track Gaps between Track Sections
     * Location sensors (IR Detectors)
     * Switch Locks
     * Switches (facing, trailing, left, right)
     * Signals and Masts
     * Maintainer Call Lamps
     * Sensors
     * Actuators
```text
    South end of Watsonville Staging Yard.  MP 90

    Yard ladder, reverse loop and departure track.  See also Watsonville North.

    < Railroad West/North                             Railroad East/South >
                                                       O-| 904Na
    Departure <================DAT= ==== 1T1========+==== =========================\
                                    |-OO 904Sab      \901                            \
                                                 903T2\                               |
    Yard Track 1 >=========d==1SAT= ===d-3T2=====d======\  YLAD                       |
                                    |-O 902sa         903\d-903T1                     |
    Yard Track 2 >=========d==2SAT= ===d 5T2=====d========\                          LOOP
                                    |-O 902sb           905\d                         |
    Yard Track 3 >=========d==3SAT= ===d 7T2======d=========\                         |
                                    |-O 902sc             907\d                       |
    Yard Track 4 >=========d==4SAT= ===d 9T2======d===========\  OO-| 902Nab         /
                                    |-O 902sd               909\=d= ===============/

                 SIG 902     SIG 904    MCall
                 L  S  R     L  S  R     ON
```
### Switches

```ebnf
sw_name = odd_ordinal ;                                (* switches are named with ODD numbers *)
tc_name = ordinal, 'T', [ ordinal ] ;                  (* Track Circuits usually end in 'T' *)
a_name  = 'T', ordinal, { ordinal } ;                  (* Actuators start with 'T' *)
cp_name = alpha, { alpha | digit | '_' } ;             (* Control Point names *)
ind_name= [ cp_name, ':' ], a_name ;                   (* Indications can optionally refer to other control points *)

direction = 'normal' | 'reverse' ;                     (* default normal *)
invert    = 'invert' ;                                 (* default is not inverted *)
acutator  = 'motor',        '=', '"', a_name,   '"' ;  (* default 'T'sw_name *)
tc        = 'trackcircuit', '=', '"', tc_name,  '"' ;  (* default is none *)
slave     = 'slaveto',      '=', '"', sw_name,  '"' ;  (* default is independent *)
indication= 'indication',   '=', '"', ind_name, '"' ;  (* default is own indication *)


attributes = { [ direction ] | [ actuator ] | [ tc ] | [ slave ] | [ invert ] | [ indication ] }
switch = '<', 'switch' 'name', '=', sw_name, attributes, '/>';

```

 ```xml
        <switches>
            <switch name="901"  trackcircuit="901T1" /> <!-- Departure track / reverse loop -->
            <switch name="903"  trackcircuit="YLAD"  /> <!-- Yard Track 1 and Yard Ladder Section (group of TCs)-->
            <switch name="905"  trackcircuit="YLAD"  /> <!-- Yard Track 2 -->
            <switch name="907"  trackcircuit="YLAD"  /> <!-- Yard Track 3 -->
            <switch name="909"  trackcircuit="YLAD"  /> <!-- Yard Track 4 -->
        </switches>
```

### Track Circuits

Attributes Required:
  * 'name'          # <alphanum>T<num>
Attributes Optional:
  * 'type'          # Default 'noreverse', 'reverse'   # Reverse Loop changes flow of traffic
  * 'indication'    # "OtherCP:1SAT" Remote feedback from another CP's indication packet
  * 'slaveto'       # Another TC, as an alias
```xml
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
```

### Sections - groupings of Track Circuits
Attributes Required:
  * 'name'          # alphanum T num  # a name for the group of TCs 

A Section is considered OCCUPIED whenever ANY of the group is occupied

```xml
        <sections>
            <section name="YLAD" >      <!-- compound collection of the following TCs -->
                <trackcircuit name="903T1" />     <trackcircuit name="903T2" />
                <trackcircuit name="905T1" />     <trackcircuit name="905T2" />
                <trackcircuit name="907T1" />     <trackcircuit name="907T2" />
                <trackcircuit name="909T1" />     <trackcircuit name="909T2" />
            </section>
        </sections>
```
### Maintainer Call and Actuators
Attributes Required:
  * 'name'          # MC num for maintainer calls -or-
  * 'name'          # alphanum for arbitrary actuators

Do something like light a lamp at the control point, state is shown in indication packets

```xml
        <actuators>
                <call         name="MC1" />
                <actuator     name="GATE1" />
                <trackpower   name="CB" />
        </actuators>
```

### Arbitrary layout feedback sensors
Attributes Required:
  * 'name'          # alphanum
```xml
        <sensors>
            <sensor name="SLIDE" />
        </sensors>
```

### Signals and Routes
In an Interlocking/Control Point...
  * Every Signal has one or more Masts associated with it
  * A Mast is typically located at one of the three entrances to a switch - points, normal or diverging)
  * A Mast governs all the routes that are reachable from it

A Route starts with the sequence of switches that must be passed through when traversing 
the control point/interlocking.  Notationally, a switch is either normal or (reversed).
Example:  In an interlocking with 3 facing point turnouts like:

          S2NABC |-O-O
    IN>    ====== ==1==== ==3==== ==5=== =====  R1
                     \     \      \
                       \     \      \
                        R2     R3      R4

Mast S2NABC controls 4 routes; it will display the MOST PERMISSIVE aspect allowed by
its set of routes.
  
      R1     1   3   5  
      R2    (1)  -   -  
      R3     1  (3)  -  
      R4     1   3  (5) 
  
this could be written as follows

```xml

            
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
 ```                                                         
        In addition to the switches that define the route, track occupancy along - or beyond - the
        route impacts route availability and locking, and the state of the signal itself (at stop,
        or cleared left or right...) also impact the aspect displayed
```xml
        <signals>
            <signal name="904" ER="False" FLEET="False" doc="Departure Track to/from LOOP">
                 <mast name="904NA" doc="Northbound LOOP to Departure Track">
                    <route name="LOOP-DT" doc="Northbound LOOP to Departure Track (usual route)">
                        <switch       name="901"                         position="N"              aspect="CLEAR" />
                        <trackcircuit name="901T1" />
                        <trackcircuit name="DAT" />
                        <signal       name="904"                         direction="LEFT"/>
                    </route>
                </mast>
        
                <mast name="904SAB"   doc="Southbound on Departure Track (reverse running) to LOOP or YLAD">
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
```
Signal Attributes Required:
  * 'name'          # even ordinal number

Signal Attributes Optional:
  * 'ER'            # Default: False
  * 'FLEET'         # Default: False
  * 'doc'           # Default: None
  * 'knockdown'     # list of Sections and/or TCs that, if OCCUPIED, causes the signal to fall back to STOP

Mast Attributes Required:
  * 'name'          # signalname direction heads    such as 902NAB or 904SA
Mast Attributes Optional:
  * 'doc'           # Default: None
      
Route Attributes Required:
  * 'name'          # unique text
Route Attributes Optional:
  * 'doc'           # Default: None

Route Elements Optional (at least 1 is required)

```
APPLIANCE (name, required state, aspect if state is matched) =>  
    if (state == required state) return aspect else return STOP  
    the ASPECT attribute defaults to CLEAR
```
The state of a route is the LEAST PERMISSIVE of all the appliances in that route
Example:
```xml
<mast name="904SAB"   doc="Southbound on Departure Track (reverse running) to LOOP or YLAD">
    <route name="RDT-LOOP" doc="Southbound (reverse running) to LOOP">
        <switch       name="901"                         position="N"               aspect="RESTRICTING" />
        <trackcircuit name="901T1" />
        <trackcircuit name="LOOP" />
        <signal       name="904"                         direction="RIGHT"/>
    </route>
</mast>
```
Example logic flow: 

    ROUTE = CLEAR # unless something in the route equation makes it less so...
    if (SW901  is N)          then ROUTE = (most restrictive of (ROUTE, DIVERGING_RESTRICTING) else ROUTE=STOP
    if (901T1  is UNOCCUPIED) then ROUTE = (most restrictive of (ROUTE, CLEAR)                 else ROUTE=STOP
    if (LOOP   is UNOCCUPIED) then ROUTE = (most restrictive of (ROUTE, CLEAR)                 else ROUTE=STOP
    if (SIG904 is RIGHT)      then ROUTE = (most restrictive of (ROUTE, CLEAR)                 else ROUTE=STOP
    return ROUTE

  4. Create/Modify the Physical I/O in the field unit
     * Use a pallet of IO Appliances: Turtle, Quad Detector, Signal Driver, Quad Sensor, Quad Actuator...
```xml
<field name="fieldunit">
     <turtle name="901" device="0" startbit="0" numbits="4" >
        <!-- implies... -->
        <input   name="901RW"      device="0" bit="0"  />  <!-- Turtle 901 - feedback REVERSE-->
        <input   name="901NW"      device="0" bit="1"  />  <!--              feedback NORMAL-->
        <input   name="901T1"      device="0" bit="2"  />  <!--              OCCUPIED-->
        <output  name="T901"       device="0" bit="3"  />  <!--              Motor Control-->
     </turtle>
     <turtle name="903" device="0" startbit="4"  numbits="4" />
     <turtle name="905" device="0" startbit="8"  numbits="4" />
     <turtle name="907" device="0" startbit="12" numbits="4" />
     <turtle name="909" device="1" startbit="1"  numbits="4" />
     <dcc name="R"      device="1" startbit="4"  numbits="4"  doc="DCC Autoreverse">
        <!-- implies -->
        <input   name="RSHORT"     device="1" bit="4"  />  <!-- AutoReverser - Indication: Short Detected -->
        <input   name="RTON"       device="1" bit="5"  />  <!--                Indication: Track is ON -->
        <input   name="ROCC"       device="1" bit="6"  />  <!--                Indication: Track is OCCUPIED -->
        <output  name="ROFF"       device="1" bit="7"  />  <!--                Control:    Power On/Off -->
     </dcc>
     <dcc        name="B" device="1" startbit="8" numbits="4" doc="DCC Booster"/>  
     <actuator   numbits="4" doc="Quad LED driver">
        <output  name="MC1"  device="1" bit="4"/>
        <output  name="XO11" device="1" bit="5"/>
        <output  name="XO12" device="1" bit="6"/>
        <output  name="XO13" device="1" bit="7"/>
     </actuator>
     <sensor     numbits="4" doc="Quad cpOD">
        <input   name="YLT"  device="2" bit="0"/>
        <input   name="DAT"  device="2" bit="1"/>
        <input   name="XI22" device="2" bit="2"/>
        <input   name="XI23" device="2" bit="3"/>
     </sensor>
     
     <signal name="902">
       <mast type="2HeadColorLight"  name="902NAB" bits="4"  device="3" bit="4" >
            <!-- Implies -->
           <output  name="902NAB1"     device="3" bit="4" />
           <output  name="902NAB2"     device="3" bit="5" />
           <output  name="902NAB3"     device="3" bit="6" />
           <output  name="902NAB4"     device="3" bit="7" />
       </mast>
       <mast type="1HeadColorLight" name="902SA" bits="2" device="3" bit="8"  />
       <mast type="1HeadColorLight" name="902SB" bits="2" device="3" bit="10" />
       <mast type="1HeadColorLight" name="902SC" bits="2" device="3" bit="12" />
       <mast type="1HeadColorLight" name="902SD" bits="2" device="3" bit="14" />
     </signal>
     
     <signal name="904">
       <mast type="1HeadColorLight" name="904NA" bits="2" device="4" bit="0" />
       <!-- mast type="1HeadColorLight" on bits 4.2 and 4.3 is unused -->
       <mast type="1HeadColorLight" name="904SAB" bits="4" device="4" bit="4" />
     </signal>
     
     <expander type="MCP23017"     address="0x00"  device="0" size="16" />
     <expander type="MCP23017"     address="0x01"  device="1" size="16" />
     <expander type="MCP23017"     address="0x02"  device="2" size="16" />
     <expander type="MCP23017"     address="0x03"  device="3" size="16" />
     <expander type="MCP23017"     address="0x04"  device="4" size="16" />
</field>
```

  5. Configure the Codeline
```xml
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
```
```xml
<indications>
     <switch       name="901"   word="0" bit="0" bits="2">
       <!-- Switches imply both a N and a R bit: -->
       <indication name="901NW" word="0" bit="0"/>
       <indication name="901RW" word="0" bit="1"/>
     </switch>
     <switch       name="903"   word="0" bit="2" bits="2"/>
     <switch       name="905"   word="0" bit="4" bits="2"/>
     <switch       name="907"   word="0" bit="6" bits="2"/>
     
     <switch       name="909"   word="1" bit="0" bits="2" />
     <signal       name="902"   word="1" bit="2" bits="3" >
     <!-- signals imply 3 bits: South not at stop, North and TIME -->
       <indication name="902SG" word="1" bit="2" />
       <indication name="902NG" word="1" bit="3" />
       <indication name="902TE" word="1" bit="4" />
     </signal>
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
```

  6. Finally, enumerate the IO expanders
```xml
<field name="fieldunit">
        ...
	    <expander type="MCP23017"     address="0x00"  device="0" size="16" />
	    <expander type="MCP23017"     address="0x01"  device="1" size="16" />
	    <expander type="MCP23017"     address="0x02"  device="2" size="16" />
	    <expander type="MCP23017"     address="0x03"  device="3" size="16" />
	    <expander type="MCP23017"     address="0x04"  device="4" size="16" />
</field>
```