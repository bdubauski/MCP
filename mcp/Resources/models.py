from django.utils import simplejson

from django.db import models
from django.conf import settings

from plato.Config.models import Config, Profile
from plato.Device.models import VMTemplate, VMHost
from plato.Network.models import SubNet
from plato.Pod.models import Pod
from plato.Config.lib import createConfig
from plato.Device.lib import createDevice
from plato.Provisioner.lib import submitConfigureJob, submitDeconfigureJob

#NOTE: these are not thread safe, there is not per-instance resource reservation
# make sure only one thing is calling these methods at a time...
# other than ready, that is thread safe

VMHOST = 1
TARGET_SUBNET = 2
TARGET_POD = 'test'

class Resource( models.Model ):
  """
Resource
  """
  name = models.CharField( max_length=50, primary_key=True )
  created = models.DateTimeField( editable=False, auto_now_add=True )
  updated = models.DateTimeField( editable=False, auto_now=True )

  def available( self ): # called first to see if resources are aviable
    return False

  def allocate( self, build, id ): # called second to allocate the resources to the project
    return None # the id of the allocated resource

  def release( self, config ):
    pass

  def ready( self, config ): # called last to see if the resources are ready to go
    config = Config.objects.get( pk=config.pk )
    return config.state == 'Configured'

  def _config( self, build, id ):
    return simplejson.dumps( { 'mcp_host': settings.MCP_HOST_NAME, 'mcp_proxy': settings.MCP_PROXY, 'mcp_build': build, 'mcp_resource': id } )

  def __unicode__( self ):
    return "Generic Resource '%s'" % self.name


class VMResource( Resource ):
  vm_template = models.CharField( max_length=50 )

  def available( self ):
    return True # for now there is allways vm space aviable

  def allocate( self, build, id ):
    address_list = []
    address_list.append( { 'interface': 'eth0', 'subnet': SubNet.objects.get( pk=TARGET_SUBNET ) } )
    config = createConfig( 'mcp_auto_%s_%s' % ( build, id ), Pod.objects.get( pk=TARGET_POD ), Profile.objects.get( pk='mcp-vmresource' ), address_list )
    config.config = self._config( build, id )
    config.save()
    return createDevice( 'VM', [ 'eth0' ], config, vmhost=VMHost.objects.get( pk=VMHOST ), vmtemplate=VMTemplate.objects.get( pk=self.vm_template ) )

  def release( self, config ):
    return submitDeconfigureJob( config, True, True )

  def __unicode__( self ):
    return "VM Resource '%s'" % self.name


class HardwareResource( Resource ):
  hardware_template = models.CharField( max_length=50 )

  def available( self ):
    return Config.objects.filter( profile='mcp-resource', hardware_profile=self.hardware_template, configured__isnull=True, configjob=None )

  def allocate( self, build, id ):
    config = Config.objects.filter( profile='mcp-resource', hardware_profile=self.hardware_template, configured__isnull=True, configjob=None )[0]
    config.config = self._config( build, id )
    config.save()
    submitConfigureJob( config )
    return config

  def release( self, config ):
    return submitDeconfigureJob( config, True, False )

  def __unicode__( self ):
    return "Hardware Resource '%s'" % self.name
