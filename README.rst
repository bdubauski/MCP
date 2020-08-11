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

you will want to setup the starting resources, first add a site, the site name (test1), should match the site id in
contractor you want to use::

  /usr/lib/mcp/util/manageResources --site-add test1

next add the network, the format is <network id>:<addressblock id>, thoes are the ids of the network and address block
in contractor you want to use::

  /usr/lib/mcp/util/manageResources --site=sjc4c08v1 --network-add=1:1

now the contractor complex to host the dynamic resources, the id (test1esx) should be the complex id on contractor.  This should be
a ESX/VCenter, Proxmox or Virtualbox complex.

  /usr/lib/mcp/util/manageResources --site=test1 --dynamic-resource-add=test1esx --dynamic-resource-add-name=vm

and finally, update the built in project (this project is used for the automatic builds triggered by test/lint, package, etc
builds) with the blueprint id from contractor::

  /usr/lib/mcp/util/manageResources --site=test1 --update-builtin=ubuntu-bionic-base

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
