from django.contrib import admin

from mcp.lib.MCPModelAdmin import MCPModelAdmin
from mcp.Projects.models import GitHubProject, Package, Build

admin.site.register( GitHubProject, MCPModelAdmin )
admin.site.register( Package, MCPModelAdmin )
admin.site.register( Build, MCPModelAdmin )
