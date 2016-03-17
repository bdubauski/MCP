import re
import hashlib

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


def config_values( job, name, index ):
  return simplejson.dumps( {
                             'mcp_host': settings.MCP_HOST,
                             'mcp_proxy': ( settings.MCP_PROXY if settings.MCP_PROXY else '' ),
                             'mcp_job_id': job.pk,
                             'mcp_resource_name': name,
                             'mcp_resource_index': index,
                             'mcp_git_url': job.project.internal_git_url,
                             'mcp_git_branch': job.branch,
                             'mcp_make_target': job.target
                            } )

def config_values_prealloc():
  return simplejson.dumps( {
                             'mcp_host': settings.MCP_HOST,
                             'mcp_proxy': ( settings.MCP_PROXY if settings.MCP_PROXY else '' ),
                             'mcp_prealloc': True
                            } )

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

  def allocate( self, job, name, quaninity, config_id_list=None ): # called second to allocate the resources to the project
    return None # the id of the allocated resource

  @staticmethod
  def release( config ):
    try:
      config = Config.objects.get( pk=config )
    except Config.DoesNotExist:
      return None # it's allready gone?

    if config.target.type == 'VM':
      return submitDeconfigureJob( config, True, True )
    else:
      job = submitDeconfigureJob( config, True, False )
      config.hostname = 'mcp-unused-%s' % ( config.pk )
      config.description = '%s.%s' % ( config.hostname, config.pod.domain )
      config.profile_id = settings.HARDWARE_PROFILE # this goes after submitDeconfigureJob so that the job has the target's deconfigure job
      config.save()
      return job

  @staticmethod
  def built( config ): # called last to see if the resources are ready to go
    try:
      config = Config.objects.get( pk=config )
    except Config.DoesNotExist:
      return True # dosen't we pretend like it's all done

    return config.status == 'Configured'

  @staticmethod
  def released( config ):
    try:
      config = Config.objects.get( pk=config )
    except Config.DoesNotExist:
      return True # dosen't Exist, all cleaned up

    return config.target.type != 'VM' and config.status == 'Provisioned'

  @staticmethod
  def config( config ):
    try:
      return Config.objects.get( pk=config )
    except Config.DoesNotExist:
      return None

  def save( self, *args, **kwargs ):
    if not re.match( '^[a-z0-9][a-z0-9\-]*[a-z0-9]$', self.name ):
      raise ValidationError( 'Invalid name' )

    super( Resource, self ).save( *args, **kwargs )

  def __unicode__( self ):
    return 'Generic Resource "%s"' % self.description

  class API:
    not_allowed_methods = ( 'CREATE', 'DELETE', 'UPDATE', 'CALL' )


class VMResource( Resource ):
  vm_template = models.CharField( max_length=50 )
  build_ahead_count = models.IntegerField( default=0 )

  def available( self, quantity ):
    subnet = SubNet.objects.get( pk=settings.TARGET_SUBNET )
    if len( subnet.unused_list ) < quantity:
      return False

    return True

  @staticmethod
  def _preallocList( pod, profile, vmtemplate ):
    return Config.objects.filter( pod=pod, profile=profile, configured__isnull=False, hostname__startswith='mcp-preallocate-', configurable__device__vmdevice__template=vmtemplate ).order_by( 'pk' )

  @staticmethod
  def _takeOver( config, job, name, index ):
    config.hostname = 'mcp-auto--%s-%s-%s' % ( job.pk, name, index )
    config.description = '%s.%s' % ( config.hostname, config.pod.domain )
    config.config_values = config_values( job, name, index )
    config.save()

  @staticmethod
  def _createNew( job, name, index, pod, profile, vmtemplate, subnet ):
    address_list = []
    address_list.append( { 'interface': 'eth0', 'subnet': subnet } )
    config = createConfig( 'mcp-auto--%s-%s-%s' % ( job.pk, name, index ), pod, profile, address_list )
    config.config_values = config_values( job, name, index )
    config.save()
    createDevice( 'VM', [ 'eth0' ], config, vmhost=VMHost.objects.get( pk=settings.VMHOST ), vmtemplate=vmtemplate )
    return config

  @staticmethod
  def _replentishPreAllocate( goal_number, pod, profile, vmtemplate, subnet, seed ):
    index = 0
    while Config.objects.filter( pod=pod, profile=profile, hostname__startswith='mcp-preallocate-' ).count() < goal_number:
      if len( subnet.unused_list ) < 1:
        return # just bail, something else will complain about this, we are just making an effort for speed here

      index += 1
      address_list = []
      address_list.append( { 'interface': 'eth0', 'subnet': subnet } )
      config = createConfig( 'mcp-preallocate--%s-%s' % ( seed, index ), pod, profile, address_list ) # so we need a unique hostname, but the number really dosen't matter as long as it is unique, so for now we will cheet and use the job id, which should be counting up to see the number
      config.config_values = config_values_prealloc()
      config.save()
      createDevice( 'VM', [ 'eth0' ], config, vmhost=VMHost.objects.get( pk=settings.VMHOST ), vmtemplate=vmtemplate )

  def allocate( self, job, name, quantity, config_id_list=None ): # for now config_id_list is ignored, VMs don't pre-exist, so can't pre pick them
    try:
      profile = Profile.objects.get( pk=self.config_profile )
    except Profile.DoesNotExist:
      raise Exception( 'Profile "%s" not found' % self.config_profile )

    try:
      vmtemplate = VMTemplate.objects.get( pk=self.vm_template )
    except VMTemplate.DoesNotExist:
      raise Exception( 'VMTemplate "%s" not found' % self.vm_template )

    pod = Pod.objects.get( pk=settings.TARGET_POD )

    config_list = list( self._preallocList( pod, profile, vmtemplate ) )

    subnet = SubNet.objects.get( pk=settings.TARGET_SUBNET )
    if len( subnet.unused_list ) < ( quantity - len( config_list ) ):
      raise Exception( 'Not enough unused Ips Available' )

    results = []
    for index in range( 0, quantity ):
      try:
        config = config_list.pop( 0 )
      except IndexError:
        config = None

      if config:
        self._takeOver( config, job, name, index )
      else:
        config = self._createNew( job, name, index, pod, profile, vmtemplate, subnet )

      results.append( config.pk )

    self._replentishPreAllocate( self.build_ahead_count, pod, profile, vmtemplate, subnet, hashlib.md5( '%s-%s-%s' % ( job.pk, name, config_id_list ) ).hexdigest()[ 0:10 ] )

    return results

  def __unicode__( self ):
    return 'VM Resource "%s"' % self.description

  class API:
    not_allowed_methods = ( 'CREATE', 'DELETE', 'UPDATE', 'CALL' )

class HardwareResource( Resource ):
  hardware_template = models.CharField( max_length=50 )

  def available( self, quantity ):
    return Config.objects.filter( profile_id=settings.HARDWARE_PROFILE, hardware_profile_id=self.hardware_template, configured__isnull=True, configjob=None ).count() >= quantity

  def allocate( self, job, name, quantity, config_id_list=None ):
    try:
      profile = Profile.objects.get( pk=self.config_profile )
    except Profile.DoesNotExist:
      raise Exception( 'Profile "%s" not found' % self.config_profile )

    if config_id_list:
      config_list = Config.objects.filter( pk__in=config_id_list, configured__isnull=True, configjob=None )
    else:
      config_list = Config.objects.all()

    config_list = config_list.filter( profile_id=settings.HARDWARE_PROFILE, hardware_profile_id=self.hardware_template, configured__isnull=True, configjob=None ).order_by( 'pk' )
    config_list = list( config_list )

    results = []
    for index in range( 0, quantity ):
      config = config_list.pop( 0 )
      config.config_values = config_values( job, name, index )
      config.profile = profile
      config.hostname = 'mcp-auto--%s-%s-%s' % ( job.pk, name, index )
      config.description = '%s.%s' % ( config.hostname, config.pod.domain )
      config.save()
      results.append( config.pk )
      submitConfigureJob( config )

    return results

  def __unicode__( self ):
    return 'Hardware Resource "%s"' % self.description

  class API:
    not_allowed_methods = ( 'CREATE', 'DELETE', 'UPDATE', 'CALL' )


class ResourceGroup( models.Model ):
  """
ResourceGroup
  """
  name = models.CharField( max_length=50, primary_key=True )
  description = models.CharField( max_length=100 )
  _config_list = models.CharField( max_length=100 )
  created = models.DateTimeField( editable=False, auto_now_add=True )
  updated = models.DateTimeField( editable=False, auto_now=True )

  @property
  def config_list( self ):
    return self._config_list.split( ',' )

  @config_list.setter
  def config_list( self, value ):
    self._config_list = ','.join( value )

  def available( self ):
    return Config.objects.filter( pk__in=self.config_list, configured__isnull=True, configjob=None ).count() == len( self.config_list )

  def save( self, *args, **kwargs ):
    if not re.match( '^[a-z0-9][a-z0-9\-]*[a-z0-9]$', self.name ):
      raise ValidationError( 'Invalid name' )

    super( ResourceGroup, self ).save( *args, **kwargs )

  def __unicode__( self ):
    return 'Resource Group "%s"' % self.description

  class API:
    not_allowed_methods = ( 'CREATE', 'DELETE', 'UPDATE', 'CALL' )


class NetworkResource( models.Model ):
  """
NetworkResource
  """
  subnet = models.IntegerField( primary_key=True )
  created = models.DateTimeField( editable=False, auto_now_add=True )
  updated = models.DateTimeField( editable=False, auto_now=True )

  def __unicode__( self ):
    return 'Network Resource for subnet "%s"' % self.subnet

  class API:
    not_allowed_methods = ( 'CREATE', 'DELETE', 'UPDATE', 'CALL' )
