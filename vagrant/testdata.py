#!/usr/bin/python -u
import os

os.environ.setdefault( "DJANGO_SETTINGS_MODULE", "mcp.settings" )

from datetime import datetime, timezone
from plato.Device.models import VMHost
from mcp.Project.models import GitHubProject

h = VMHost()
h.full_clean()
h.save()

p = GitHubProject()
p.name = 'packrat-test'
p.last_checked = datetime.now( timezone.utc )
p._org = 'packrat'
p._repo = 'test'
p.full_clean()
p.save()
