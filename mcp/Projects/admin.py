from django.contrib import admin

from mcp.Projects.models import GitHubProject, Package, Build, BuildDependancy, BuildResource

admin.site.register( GitHubProject )
admin.site.register( Package )
admin.site.register( Build )
admin.site.register( BuildDependancy )
admin.site.register( BuildResource )
