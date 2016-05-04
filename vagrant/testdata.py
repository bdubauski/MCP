#!/usr/bin/python -u
import os

os.environ.setdefault( "DJANGO_SETTINGS_MODULE", "mcp.settings" )

from django.contrib.auth.models import User
u = User.objects.get( username__exact='root' )
u.set_password( 'root' )
u.save()

from django.utils.timezone import utc
from datetime import datetime
from plato.Device.models import VMHost
from mcp.Project.models import GitHubProject

h = VMHost()
h.save()

p = GitHubProject()
p.name = 'packrat-test'
p.last_checked = datetime.utcnow().replace( tzinfo=utc )
p._org = 'packrat'
p._repo = 'test'
p.save()
