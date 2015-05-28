from django.contrib import admin

from mcp.lib.MCPModelAdmin import MCPModelAdmin
from mcp.Processor.models import QueueItem, BuildJob

admin.site.register( QueueItem, MCPModelAdmin )
admin.site.register( BuildJob, MCPModelAdmin )
