from django.conf.urls import patterns, include, url
from django.contrib import admin
from cinp.django_plugin import DjangoAPI

api = DjangoAPI( '/api/v1/' )
api.registerApp( 'Processor', 'v1' )
api.registerApp( 'Project', 'v1' )
api.registerApp( 'Resource', 'v1' )
api.registerApp( 'Users', 'v1' )

admin.autodiscover()

urlpatterns = patterns('',
    url( r'^$', 'mcp.views.index' ),
    url( r'^oauth', 'mcp.views.oauth' ),
    url( r'^admin/', include( admin.site.urls ) ),
    url( r'^api/', include( api.urls ) ),
)
