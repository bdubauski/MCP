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
