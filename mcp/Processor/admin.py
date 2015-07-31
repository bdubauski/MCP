from django.contrib import admin

from mcp.Processor.models import QueueItem, BuildJob, Promotion

admin.site.register( QueueItem )
admin.site.register( BuildJob )
admin.site.register( Promotion )
