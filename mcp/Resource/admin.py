from django.contrib import admin

from mcp.Resource.models import VMResource, HardwareResource, ResourceGroup, NetworkResource

admin.site.register( VMResource )
admin.site.register( HardwareResource )
admin.site.register( ResourceGroup )
admin.site.register( NetworkResource )
