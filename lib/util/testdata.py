#!/usr/bin/env python3
import os

os.environ.setdefault( 'DJANGO_SETTINGS_MODULE', 'mcp.settings' )

import django
django.setup()

from datetime import datetime, timezone

from mcp.Project.models import GitHubProject
from mcp.Resource.models import NetworkResource

print( 'Loading Projects...' )
for name in ( 'test',):  # 'mcp', 'nullunit' ):
  project = GitHubProject( name=name, _org='packrat', _repo=name )
  project.last_checked = datetime.now( timezone.utc )
  project.full_clean()
  project.save()

print( 'Loading Networks...' )
for name in ( 'main',  ): # ( 'mcp', 'primary' ):
  resource = NetworkResource( name=name )
  resource.full_clean()
  resource.save()
