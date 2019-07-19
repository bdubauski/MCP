#!/usr/bin/env python3
import os

if __name__ == '__main__':
  os.environ.setdefault( 'DJANGO_SETTINGS_MODULE', 'mcp.settings' )

  import django
  django.setup()

from django.contrib.auth.models import User, Permission


def load_users():
  User.objects.create_superuser( username='root', email='root@none.com', password='root' )

  u = User.objects.create_user( 'manager', password='manager' )
  for name in ( 'can_build', 'can_ran', 'can_ack' ):
    u.user_permissions.add( Permission.objects.get( codename=name ) )

  u = User.objects.create_user( 'dev', password='dev' )
  for name in ( 'can_ack', ):
    u.user_permissions.add( Permission.objects.get( codename=name ) )


def load():
  print( 'Creating Users...' )
  load_users()


if __name__ == '__main__':
  load()
