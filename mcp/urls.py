from django.conf.urls import patterns, include, url
from django.contrib import admin
from cinp.django_plugin import DjangoAPI

api = DjangoAPI( '/api/v1/' )
api.registerApp( 'Processor', 'v1' )
api.registerApp( 'Project', 'v1' )
api.registerApp( 'Resource', 'v1' )
# Auth is not registered, #1 it is building in the the cinp django_plugin, and #2 it's tracked internally
admin.autodiscover()

urlpatterns = patterns('',
    url( r'^$', 'mcp.views.index' ),
    url( r'^admin/', include( admin.site.urls ) ),
    url( r'^api/', include( api.urls ) ),
)
