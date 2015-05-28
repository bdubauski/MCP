from django.contrib import admin

from mcp.lib.MCPModelAdmin import MCPModelAdmin
from mcp.Resources.models import VMResource, HardwareResource

admin.site.register( VMResource, MCPModelAdmin )
admin.site.register( HardwareResource, MCPModelAdmin )
