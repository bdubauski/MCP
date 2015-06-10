import re

from django.utils import simplejson

from django.core.exceptions import ObjectDoesNotExist, ValidationError
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
TARGET_SUBNET = 1
TARGET_POD = 'mcp'

class Resource( models.Model ):
  """
Resource
  """
  name = models.CharField( max_length=50, primary_key=True )
  description = models.CharField( max_length=100 )
  config_profile = models.CharField( max_length=50 )
  created = models.DateTimeField( editable=False, auto_now_add=True )
  updated = models.DateTimeField( editable=False, auto_now=True )

  @property
  def native( self ):
    try:
      return self.vmresource
    except ObjectDoesNotExist:
      pass

    try:
      return self.hardwareresource
    except ObjectDoesNotExist:
      pass

    return self

  def available( self, quantity ): # called first to see if resources are aviable
    return False

  def allocate( self, build, id, name, quaninity ): # called second to allocate the resources to the project
    return None # the id of the allocated resource

  @staticmethod
  def release( config ):
    config = Config.objects.get( pk=config )
    if config.target.type == 'VM':
      return submitDeconfigureJob( config, True, True )
    else:
      return submitDeconfigureJob( config, True, False )

  @staticmethod
  def built( config ): # called last to see if the resources are ready to go
    config = Config.objects.get( pk=config )
    return config.status == 'Configured'

  @staticmethod
  def released( config ):
    try:
      config = Config.objects.get( pk=config )
    except Config.DoesNotExist:
      return True # dosen't Exist, all cleaned up

    return config.target.type != 'VM' and config.status == 'Provisioned'

  def _config( self, build, name, index ):
    return simplejson.dumps( { 'mcp_host': settings.MCP_HOST_NAME, 'mcp_proxy': ( settings.MCP_PROXY if settings.MCP_PROXY else '' ), 'mcp_build': build.name, 'mcp_resource_name': name, 'mcp_resource_index': index } )

  def save( self, *args, **kwargs ):
    if not re.match( '^[a-z0-9][a-z0-9\-]*[a-z0-9]$', self.name ):
      raise ValidationError( 'Invalid name' )

    super( Resource, self ).save( *args, **kwargs )

  def __unicode__( self ):
    return 'Generic Resource "%s"' % self.description


class VMResource( Resource ):
  vm_template = models.CharField( max_length=50 )

  def available( self, quantity ):
    return True # for now there is allways vm space aviable

  def allocate( self, build, id, name, quaninity ):
    results = []
    for index in range( 0, quaninity ):
      address_list = []
      address_list.append( { 'interface': 'eth0', 'subnet': SubNet.objects.get( pk=TARGET_SUBNET ) } )
      config = createConfig( 'mcp-auto--%s-%s--%s-%s' % ( build.name, id, name, index ), Pod.objects.get( pk=TARGET_POD ), Profile.objects.get( pk=self.config_profile ), address_list )
      config.config_values = self._config( build, name, index )
      config.save()
      createDevice( 'VM', [ 'eth0' ], config, vmhost=VMHost.objects.get( pk=VMHOST ), vmtemplate=VMTemplate.objects.get( pk=self.vm_template ) )
      results.append( config.pk )

    return results

  def __unicode__( self ):
    return 'VM Resource "%s"' % self.description


class HardwareResource( Resource ):
  hardware_template = models.CharField( max_length=50 )

  def available( self, quantity ):
    return Config.objects.filter( profile='mcp-resource', hardware_profile=self.hardware_template, configured__isnull=True, configjob=None ).count() > quantity

  def allocate( self, build, id, name, quaninity ):
    results = []
    config_list = Config.objects.filter( profile='mcp-resource', hardware_profile=self.hardware_template, configured__isnull=True, configjob=None )
    for index in range( 0, quaninity ):
      config = config_list.pop()
      config.config_values = self._config( build, name, index )
      config.profile = Profile.objects.get( pk=self.config_profile )
      config.hostname = 'mcp-auto--%s-%s--%s-%s' % ( build.name, id, name, index )
      config.description = '%s.%s' % ( config.hostname, config.pod.domain )
      config.save()
      results.append( config.pk )
      submitConfigureJob( config )

    return results

  def __unicode__( self ):
    return 'Hardware Resource "%s"' % self.description
