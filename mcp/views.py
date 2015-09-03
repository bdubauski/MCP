from django.http import HttpResponse
from django.template import Template, Context

from mcp.Project.models import Commit
from mcp.Resource.models import HARDWARE_PROFILE
from mcp.Processor.models import QueueItem, BuildJob, Promotion
from plato.Config.models import Config

def index( request ):
  t = Template( """<html>
<head>
<title>MCP</title>
</head>
<body>
<a href="/admin/">Admin</a><br/>
<a href="/status">Status</a><br/>
Dependancy Graph <a href="/static/graph.png">(png)</a> <a href="/static/graph.pdf">(pdf)</a></br>
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
<tr><th>Job Id</th><th>Build</th><th>State</th><th>Status</th><th>Manual</th><th>Last Updated</th><th>Target</th><th>Project</th><th>Created</th></tr>
{% for item in job_list %}
<tr><td>{{ item.pk }}</td><td>{{ item.build.name }}</td><td>{{ item.state }}</td><td>{{ item.resources }}</td><td>{{ item.manual }}</td><td>{{ item.updated }}</td><td>{{ item.target }}</td><td>{{ item.project.name }}</td><td>{{ item.created }}</td></tr>
{% endfor %}
</table>
<b>Queued Jobs</b>
<table border="1">
<tr><th>Queue Id</th><th>Priority</th><th>Manual</th><th>Build</th><th>Status</th><th>Last Updated</th><th>Target</th><th>Project</th><th>Branch</th><th>Created</th></tr>
{% for item in queue_list %}
<tr><td>{{ item.pk }}</td><td>{{ item.priority }}</td><td>{{ item.manual }}</td><td>{{ item.build.name }}</td><td>{{ item.resource_status }}</td><td>{{ item.updated }}</td><td>{{ item.target }}</td><td>{{ item.project.name }}</td><td>{{ item.branch }}</td><td>{{ item.created }}</td></tr>
{% endfor %}
</table>
</table>
<b>Promotion Jobs</b>
<table border="1">
<tr><th>Promotion Id</th><th>Packages/Versions</th><th>To State</th><th>Created</th></tr>
{% for item in promtion_list %}
<tr><td>{{ item.pk }}</td><td>{% for pkg_version in item.promotionpkgversion_set.all %} {{ pkg_version.package_version.package.name }}({{ pkg_version.package_version.version }}){% endfor %}</td><td>{{ item.to_state }}</td><td>{{ item.created }}</td></tr>
{% endfor %}
</table>
<b>Commit List</b>
<table border="1">
<tr><th>Commit Id</th><th>Git URL</th><th>Branch</th><th>Commit</th><th>Lint At</th><th>Lint Status</th><th>Test At</th><th>Test Status</th><th>Build At</th><th>Build Status</th><th>Last Updated</th><th>Created</th></tr>
{% for item in commit_list %}
<tr><td>{{ item.pk }}</td><td>{{ item.project.githubproject.github_url }}</td><td>{{ item.branch }}</td><td>{{ item.commit }}</td><td>{{ item.lint_at }}</td><td>{{ item.lint_results }}</td><td>{{ item.test_at }}</td><td>{{ item.test_results }}</td><td>{{ item.build_at }}</td><td>{{ item.build_results }}</td><td>{{ item.updated }}</td><td>{{ item.created }}</td></tr>
{% endfor %}
</table>
<b>Unused Resources</b>
<table border="1">
<tr><th>Config Id</th><th>Status</th><th>Config Profile</th><th>Hardware Profile</th></tr>
{% for item in unused_list %}
<tr><td>{{ item.pk }}</td><td>{{ item.status }}</td><td>{{ item.profile.name }}</td><td>{{ item.hardware_profile.name }}</td></tr>
{% endfor %}
</table>
Generated at {% now "jS F Y H:i" %}
</body>
</html>""" )

  c = Context( {
                 'job_list': BuildJob.objects.all().order_by( 'pk' ),
                 'queue_list': QueueItem.objects.all().order_by( '-priority' ),
                 'promtion_list': Promotion.objects.all().order_by( 'pk' ),
                 'commit_list': Commit.objects.filter( done_at__isnull=True ).order_by( 'pk' ),
                 'unused_list': Config.objects.filter( profile=HARDWARE_PROFILE, configured__isnull=True ).order_by( 'pk' )
               } )
  return HttpResponse( t.render( c ) )
