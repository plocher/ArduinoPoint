<H2> Control Point Documentation for ${cp.name} </H2>

<pre>
% for d in cp.DocList():
    ${d | h}
%endfor
</pre>

<H2> Code Line for ${cp.name} (${cp.getNode()}) </H2>
<H3> Control Packet </H3>

${ cp.controls.towiki() }

<H3> Indication Packet </H3>
${cp.indications.towiki()}

% for d in cp.getDependencyList():
    % if d.name != cp.name:
<p> Depends on ${d.name} </p>
${ d.indications.towiki() }
    %endif
%endfor

<H2> Layout Connections for ${cp.name} </H2>
% for k, v in cp.FieldunitList():
    % if v.name == 'fieldunit':
        <H3> Expanders </H3>
        <H4> Assignmenmts  </H4>
${ v.towiki() }

        <H4> Wiring  </H4>
${ v.expanders.toDetailedWiki() }
    %endif
%endfor

<H2> Signals and Routes for ${cp.name} </H2>
% for fk, fv in cp.field.children.items():
    % if fk == 'fieldunit':
        % for smname, sm in fv.signals.children.items():
            <% signalFullName = '{cpname}:{smname}'.format(cpname=cp.name, smname=smname) %>
            <% siga = sm.sig %>
            <% docstring = siga.doc %>
            % if docstring is None:
                <% docstring = '' %>
            % endif
<H3> Signal ${smname}: ${docstring} </H3>

<p>
            % if (siga.fleet is not None) and (siga.er is not None) and (siga.fleet.lower() != 'false') and (siga.er.lower() != 'false'):
                Stick Relays [(]
                %if (siga.fleet.lower() == 'true') and (siga.er.lower() == 'true'):
                    FLEET and ER
                %elif (siga.fleet.lower() == 'true') and (siga.er.lower() != 'true'):
                    FLEET
                %elif (siga.fleet.lower() == 'true') and (siga.er.lower() != 'true'):
                    ER
                %endif
                ]
            %else:
                Stick Relays [No Engine Return, No Fleeting]
            %endif
</p>

            % for shname, sh in sm.children.items():
                <% mastFullName = '{cpname}:{shname}'.format(cpname=cp.name, shname=shname) %>
                <% heada = siga.getMast(mastFullName) %>
                <% docstring = heada.doc %>
                %if docstring is None:
                    <% docstring = '' %>
                %endif
                    <H4>  Mast ${shname}</H4>
                    Type: ${sh.type} <br \>${docstring | h} <br \>
<p></p>

<table border="1">
                % for rk, rv in heada.route.children.items():
                    <% docstring = rv.doc %>
                    % if docstring is None:
                        <% docstring = ''  %>
                    %endif
<tr>
    <td align="left" colspan=3>
    &nbsp;&nbsp;Route
    <b>${rk}</b>
    <br \>&nbsp;&nbsp;${docstring}
                    % if rv.default_aspect is None:
                        <% longform=True %>
                    %else:
                        <% longform=False %>
    <br \>&nbsp;&nbsp;Aspect <b>${rv.default_aspect}</b>
                    %endif
    </td>
</tr>
                        <!-- table border="1" -->
<tr>
    <th>Switches  </th>
    <th>Tracks    </th>
    <th>Signals   </th>
</tr>

<tr>
<td>
                        % for val, item in rv.children.items():
                            % if item.mytype == "SW_Route":
&nbsp;&nbsp;<code>
${ item.toHTML(longform) }
</code>&nbsp;&nbsp;
<BR>
                            % endif
                        % endfor
</td>
<td>
                        % for val, item in rv.children.items():
                            % if item.mytype != "SW_Route" and item.mytype != "SIG_Route":
&nbsp;&nbsp;<code>${ item.toHTML(longform) }</code>&nbsp;&nbsp;
<BR>
                            % endif
                        % endfor
</td>
<td>
                        % for val, item in rv.children.items():
                            % if item.mytype == "SIG_Route":
&nbsp;&nbsp;<code>${ item.toHTML(longform) } </code>&nbsp;&nbsp;
<BR>
                            % endif
                        % endfor
</td>
</tr><!-- /table -->
<tr> <td colspan="3">&nbsp;</td></tr>

<p>
</p>

                %endfor
</table>
<p>&nbsp;
</p>
            %endfor
        %endfor
    %endif
%endfor


