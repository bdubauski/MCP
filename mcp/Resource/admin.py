from django.contrib import admin

from mcp.Resource.models import VMResource, HardwareResource, ResourceGroup

admin.site.register( VMResource )
admin.site.register( HardwareResource )
admin.site.register( ResourceGroup )
