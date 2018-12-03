#!/usr/bin/python3
import os

os.environ.setdefault( 'DJANGO_SETTINGS_MODULE', 'mcp.settings' )

import django
django.setup()

from django.contrib.auth.models import User
u = User.objects.get( username__exact='root' )
u.set_password( 'root' )
u.full_clean()
u.save()
