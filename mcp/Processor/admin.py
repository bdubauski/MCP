from django.contrib import admin

from mcp.Processor.models import QueueItem, BuildJob

admin.site.register( QueueItem )
admin.site.register( BuildJob )
