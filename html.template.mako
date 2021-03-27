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
    ${d}
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

                <p> ${signalFullName}
            % if (siga.fleet is not None) and (siga.er is not None) and (siga.fleet.lower() != 'false') and (siga.er.lower() != 'false'):
                [${siga.fleet.lower()}, ${siga.er.lower()}] (
                %if (siga.fleet.lower() == 'true') and (siga.er.lower() == 'true'):
                    FLEET and ER
                %elif (siga.fleet.lower() == 'true') and (siga.er.lower() != 'true'):
                    FLEET
                %elif (siga.fleet.lower() == 'true') and (siga.er.lower() != 'true'):
                    ER
                %endif
                )
            %else:
                (No Engine Return, No Fleeting)
            %endif
                </p>
                <ul>

            % for shname, sh in sm.children.items():
                <% mastFullName = '{cpname}:{shname}'.format(cpname=cp.name, shname=shname) %>
                <% heada = siga.getMast(mastFullName) %>
                <% docstring = heada.doc %>
                %if docstring is None:
                    <% docstring = '' %>
                %endif
                    <li> Mast <b>${shname}</b> ${sh.type} ${docstring} </li>
                    <p></p>

                    <ul>
                % for rk, rv in heada.route.children.items():
                    <% docstring = rv.doc %>
                    % if docstring is None:
                        <% docstring = ''  %>
                    %endif

                    % if rv.default_aspect is None:
                        <% longform=True %>
                            <li> Route <b>${rk}</b>  - ${docstring} </li>
                    %else:
                        <% longform=False %>
                            <li> Route <b>${rk}</b> Aspect ${rv.default_aspect}  - ${docstring}</li>
                    %endif
                        <p></p>
                        <ul>
                        % for val, item in rv.children.items():
                            <li><code>${ item.toHTML(longform) }</code></li>
                        % endfor
                        </ul>
                        <p></p>

                %endfor
                    </ul>
            %endfor
                </ul>
        %endfor
    %endif
%endfor
    </code>
</blockquote>
</body>
</html>

