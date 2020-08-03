MCP
===

System for Unit Testing, Packaging, Integration Testing and Documentation.

The only "Configuration" is to register the project with MCP, all other configuration, scripts, etc are via the Makefile(s)
in the code of the project.

See the docs dir for more info.


Install
-------

as root

from package::

  dpkg -i mcp_*.deb

from source::

  DESTDIR=/ make install

then::

  su postgres -c "echo \"CREATE ROLE packrat WITH PASSWORD 'mcp' NOSUPERUSER NOCREATEDB NOCREATEROLE LOGIN;\" | psql"
  su postgres -c "createdb -O mcp mcp"
  /usr/lib/mcp/util/manage.py migrate
  /usr/lib/mcp/setup/setupWizzard


Now we need to create the MCP user, on the contractor host::

  /usr/lib/contractor/util/manage.py shell
  from django.contrib.auth.models import User, Permission
  user = User.objects.create_user('mcp', 'mcp@mcp.test', 'mcp')
  user.user_permissions.add( Permission.objects.get( codename='can_create_foundation', content_type__app_label='Building' ) )
  user.user_permissions.add( Permission.objects.get( codename='add_structure', content_type__app_label='Building' ) )
  user.user_permissions.add( Permission.objects.get( codename='delete_structure', content_type__app_label='Building' ) )
  user.user_permissions.add( Permission.objects.get( codename='delete_foundation', content_type__app_label='Building' ) )
  user.user_permissions.add( Permission.objects.get( codename='add_realnetworkinterface', content_type__app_label='Utilities' ) )
  user.user_permissions.add( Permission.objects.get( codename='add_address', content_type__app_label='Utilities' ) )
  user.user_permissions.add( Permission.objects.get( codename='can_create_foundation_job', content_type__app_label='Building' ) )
  user.user_permissions.add( Permission.objects.get( codename='can_create_structure_job', content_type__app_label='Building' ) )
  user.user_permissions.add( Permission.objects.get( codename='change_structure', content_type__app_label='Building' ) )
  user.user_permissions.add( Permission.objects.get( codename='can_config_structure', content_type__app_label='Building' ) )
  user.user_permissions.add( Permission.objects.get( codename='add_structurebox', content_type__app_label='PostOffice' ) )
  user.user_permissions.add( Permission.objects.get( codename='add_foundationbox', content_type__app_label='PostOffice' ) )
