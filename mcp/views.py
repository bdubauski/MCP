from django.http import HttpResponse
from django.template import Template, Context

from mcp.Processor.models import QueueItem, BuildJob

def index( request ):
  t = Template( """<html>
<head>
<title>MCP</title>
</head>
<body>
<a href="/admin/">Admin</a><br/>
<a href="/status">Status</a><br/>
</body>
</html>""" )

  c = Context( {} )
  return HttpResponse( t.render( c ) )

def status( request ):
  t = Template( """<html>
<head>
<title>MCP - Status</title>
<meta http-equiv="refresh" content="60"/>
</head>
<body>
<b>Build Jobs</b>
<table border="1">
<tr><th>Job Id</th><th>Build</th><th>State</th><th>Status</th><th>Manual</th><th>Last Updated</th><th>Target</th><th>Git URL</th><th>Created</th></tr>
{% for item in job_list %}
<tr><td>{{ item.pk }}</td><td>{{ item.build.name }}</td><td>{{ item.state }}</td><td>{{ item.resources }}</td><td>{{ item.manual }}</td><td>{{ item.updated }}</td><td>{{ item.target }}</td><td>{{ item.git_url }}</td><td>{{ item.created }}</td></tr>
{% endfor %}
</table>
<b>Queued Jobs</b>
<table border="1">
<tr><th>Queue Id</th><th>Priority</th><th>Manual</th><th>Build</th><th>Status</th><th>Last Updated</th><th>Target</th><th>Git URL</th><th>Created</th></tr>
{% for item in queue_list %}
<tr><td>{{ item.pk }}</td><td>{{ item.priority }}</td><td>{{ item.manual }}</td><td>{{ item.build.name }}</td><td>{{ item.resource_status }}</td><td>{{ item.updated }}</td><td>{{ item.target }}</td><td>{{ item.git_url }}</td><td>{{ item.created }}</td></tr>
{% endfor %}
</table>
Generated at {% now "jS F Y H:i" %}
</body>
</html>""" )

  c = Context( {
                 'job_list': BuildJob.objects.all(),
                 'queue_list': QueueItem.objects.all().order_by( 'priority' ),
               } )
  return HttpResponse( t.render( c ) )
