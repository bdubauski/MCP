from django.contrib import admin

from mcp.Processor.models import QueueItem, BuildJob, Promotion, PromotionPkgVersion, PromotionBuild

admin.site.register( QueueItem )
admin.site.register( BuildJob )
admin.site.register( Promotion )
admin.site.register( PromotionPkgVersion )
admin.site.register( PromotionBuild )
