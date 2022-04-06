<html>
<title>${cp.name}</title>
<style>
table {{
  border: 2px solid black;
  border-collapse: collapse;
}}

td {{
  border: 1px solid grey;
}}

th {{
  border: 1px solid black;
  background: grey10;
}}

</style>
<body>

<H1>Control Point Documentation for ${cp.name}</H1>

<pre>
% for d in cp.DocList():
    ${d | h}
%endfor
</pre>

<H1>Code Line for ${cp.name} (${cp.getNode()})</H1>
<H2>Control Packet</H2>

<blockquote>
    ${ cp.controls.towiki() }
</blockquote>

<H2>Indication Packet</H2>
<blockquote>
    ${cp.indications.towiki()}
</blockquote>

% for d in cp.getDependencyList():
    % if d.name != cp.name:
    <p> Depends on ${d.name} </p>
    ${ d.indications.towiki() }
    %endif
%endfor

<H1>Layout Connections for ${cp.name}</H1>
% for k, v in cp.FieldunitList():
    % if v.name == 'fieldunit':
        <H2>Expanders</H2>
        <H3>Assignmenmts</H3>
        <blockquote>
            ${ v.towiki() }
        </blockquote>

        <H3>Wiring</H3>
        <blockquote>
            ${ v.expanders.toDetailedWiki() }
        </blockquote>
    %endif
%endfor

<H1>Signals and Routes for ${cp.name}</H1>
<blockquote>
    <code>
% for fk, fv in cp.field.children.items():
    % if fk == 'fieldunit':
        % for smname, sm in fv.signals.children.items():
            <% signalFullName = '{cpname}:{smname}'.format(cpname=cp.name, smname=smname) %>
            <% siga = sm.sig %>
            <% docstring = siga.doc %>
            % if docstring is None:
                <% docstring = '' %>
            % endif
                <H2> Signal ${smname}: ${docstring} </H2>
                <blockquote>
                <p>
            % if (siga.fleet is not None) and (siga.er is not None) and (siga.fleet.lower() != 'false') and (siga.er.lower() != 'false'):
                Stick Relays [
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
                    <H3>  Mast ${shname}</H3>
                    <blockquote>
                    Type: ${sh.type} <br \>${docstring | h} <br \>
                    <p></p>

                    <table border="1">
                % for rk, rv in heada.route.children.items():
                    <% docstring = rv.doc %>
                    % if docstring is None:
                        <% docstring = ''  %>
                    %endif
                        <tr><th align="left" colspan="3"><p>&nbsp;</p>
                    % if rv.default_aspect is None:
                        <% longform=True %>
                            <p>&nbsp;&nbsp;Route <b>${rk}</b>  - ${docstring}</p>
                    %else:
                        <% longform=False %>
                            <p>&nbsp;&nbsp;Route <b>${rk}</b> Aspect ${rv.default_aspect}  - ${docstring}</p>
                    %endif
                        <p>&nbsp;</p></th></tr>
                        <!-- table border="1" -->
                            <tr><th>Switches</th><th>Tracks</th><th>Signals</th></tr>
                            <tr><td>
                        % for val, item in rv.children.items():
                            % if item.mytype == "SW_Route":
                            <code>${ item.toHTML(longform) }</code><BR>
                            % endif
                        % endfor
                        </td><td>
                        % for val, item in rv.children.items():
                            % if item.mytype != "SW_Route" and item.mytype != "SIG_Route":
                            <code>${ item.toHTML(longform) }</code><BR>
                            % endif
                        % endfor
                        </td><td>
                        % for val, item in rv.children.items():
                            % if item.mytype == "SIG_Route":
                            <code>${ item.toHTML(longform) }</code><BR>
                            % endif
                        % endfor
                        </td></tr><!-- /table -->
                        <p></p>

                %endfor
                    </table>
                    </blockquote>
                    <p>&nbsp;</p>
            %endfor
            </blockquote>
        %endfor
    %endif
%endfor
    </code>
</blockquote>
</body>
</html>

