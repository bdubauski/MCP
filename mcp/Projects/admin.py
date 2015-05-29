from django.contrib import admin

from mcp.Projects.models import GitHubProject, Package, Build

admin.site.register( GitHubProject )
admin.site.register( Package )
admin.site.register( Build )
