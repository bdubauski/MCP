from django.contrib import admin

from mcp.Resources.models import VMResource, HardwareResource

admin.site.register( VMResource )
admin.site.register( HardwareResource )
