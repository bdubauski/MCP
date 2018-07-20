from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models
from django.conf import settings
from django.apps import apps

from cinp.orm_django import DjangoCInP as CInP

from mcp.lib.t3kton import getContractor
from mcp.fields import name_regex

# NOTE: these are not "thread safe", there is not per-instance resource reservation
# make sure only one thing is calling these methods at a time...
# other than ready, that is thread safe


cinp = CInP( 'Resource', '0.1' )


@cinp.model( not_allowed_verb_list=[ 'CREATE', 'DELETE', 'UPDATE', 'CALL' ] )
class Site( models.Model ):
  """
Site
  """
  name = models.CharField( max_length=40, primary_key=True )
  created = models.DateTimeField( editable=False, auto_now_add=True )
  updated = models.DateTimeField( editable=False, auto_now=True )

  def clean( self, *args, **kwargs ):
    super().clean( *args, **kwargs )
    errors = {}

    if not name_regex.match( self.name ):
      errors[ 'name' ] = 'Invalid'

    if errors:
      raise ValidationError( errors )

  @cinp.check_auth()
  @staticmethod
  def checkAuth( user, verb, id_list, action=None ):
    return True

  def __str__( self ):
    return 'Site "{0}"'.format( self.name )


@cinp.model( not_allowed_verb_list=[ 'CREATE', 'DELETE', 'UPDATE', 'CALL' ] )
class Resource( models.Model ):
  """
Resource
  """
  name = models.CharField( max_length=50, primary_key=True )
  priority = models.IntegerField( default=50 )  # higher the value, higer the priority
  description = models.CharField( max_length=100 )
  blueprint = models.CharField( max_length=40 )
  site = models.ForeignKey( Site, on_delete=models.CASCADE )
  created = models.DateTimeField( editable=False, auto_now_add=True )
  updated = models.DateTimeField( editable=False, auto_now=True )

  @property
  def subclass( self ):
    try:
      return self.dynamicresource
    except ObjectDoesNotExist:
      pass

    try:
      return self.staticresource
    except ObjectDoesNotExist:
      pass

    return self

  def available( self, quantity ):  # called first to see if resources are aviable
    return False

  def allocate( self, job, name, quantity ):  # called second to allocate the resources to the project
    return None  # the id of the allocated resource

  def build( self, instance ):
    raise Exception( 'Not Implemented' )

  def release( self, instance ):
    raise Exception( 'Not Implemented' )

  @cinp.check_auth()
  @staticmethod
  def checkAuth( user, verb, id_list, action=None ):
    return True

  def clean( self, *args, **kwargs ):
    super().clean( *args, **kwargs )
    errors = {}

    if not name_regex.match( self.name ):
      errors[ 'name' ] = 'Invalid'

    if errors:
      raise ValidationError( errors )

  def __str__( self ):
    return 'Generic Resource "{0}"'.format( self.description )


@cinp.model( not_allowed_verb_list=[ 'CREATE', 'DELETE', 'UPDATE', 'CALL' ] )
class DynamicResource( Resource ):
  build_ahead_count = models.IntegerField( default=0 )
  complex = models.CharField( max_length=40 )

  def available( self, quantity ):
    return True

  def _takeOver( self, instance, buildjob, name, index ):
    instance.buildjob = buildjob
    instance.name = name
    instance.index = index
    instance.hostname = 'mcp-auto--{0}-{1}-{2}'.format( buildjob.pk, name, index )
    instance.full_clean()
    instance.save()

    contractor = getContractor()
    contractor.updateConfig( instance.structure_id, instance.config_values, instance.hostname )

  def _createNew( self, network, buildjob, name, index ):
    Instance = apps.get_model( 'Processor', 'Instance' )

    instance = Instance( resource=self, network=network )
    instance.buildjob = buildjob
    instance.name = name
    instance.index = index
    instance.hostname = 'mcp-auto--{0}-{1}-{2}'.format( buildjob.pk, name, index )
    instance.full_clean()
    instance.save()

    instance.build()

  def _replentishPreAllocate( self, network ):
    Instance = apps.get_model( 'Processor', 'Instance' )
    while self.instance_set.filter( buildjob__isnull=True ).count() < self.build_ahead_count:  # TODO: make sure there is room for more vms in the subnet
      instance = Instance( resource=self, network=network )
      instance.hostname = 'mcp-preallocate--{0}-'.format( self.name )
      instance.full_clean()
      instance.save()

      instance.hostname = 'mcp-preallocate--{0}-{1}'.format( self.name, instance.pk )
      instance.full_clean()
      instance.save()

      instance.build()

  def allocate( self, job, name, quantity, network ):
    instance_list = self.instance_set.filter( buildjob__isnull=True, network=network ).order_by( 'pk' ).iterator()

    for index in range( 0, quantity ):
      instance = next( instance_list, None )

      if instance is not None:
        self._takeOver( instance, job, name, index )
      else:
        self._createNew( network, job, name, index )

    self._replentishPreAllocate( network )

  def build( self, instance ):
    contractor = getContractor()

    ( foundation_id, structure_id ) = contractor.createInstance( self.site.name, self.complex, self.blueprint, instance.hostname, instance.config_values, instance.network.name )
    instance.foundation_id = foundation_id
    instance.structure_id = structure_id
    instance.full_clean()
    instance.save()
    contractor.registerWebHook( instance, True )
    contractor.createFoundation( instance.foundation_id )

  def release( self, instance ):
    contractor = getContractor()
    contractor.registerWebHook( instance, False )
    contractor.destroyStructure( instance.structure_id )

  @cinp.check_auth()
  @staticmethod
  def checkAuth( user, verb, id_list, action=None ):
    return True

  def __str__( self ):
    return 'Dynmaic Resource "{0}"'.format( self.description )


@cinp.model( not_allowed_verb_list=[ 'CREATE', 'DELETE', 'UPDATE', 'CALL' ] )
class StaticResource( Resource ):

  def available( self, quantity ):
    return Config.objects.filter( profile_id=settings.HARDWARE_PROFILE, hardware_profile_id=self.hardware_template, configured__isnull=True, configjob=None ).count() >= quantity

  def allocate( self, job, name, quantity, network ):
    if network != self.network:
      raise ValueError( 'target network not attached to static resource network' )

    try:
      profile = Profile.objects.get( pk=self.config_profile )
    except Profile.DoesNotExist:
      raise Exception( 'Profile "{0}" not found'.format( self.config_profile ) )

    config_list = Config.objects.all()
    config_list = config_list.filter( profile_id=settings.HARDWARE_PROFILE, hardware_profile_id=self.hardware_template, configured__isnull=True, configjob=None ).order_by( 'pk' )
    config_list = list( config_list )

    results = []
    for index in range( 0, quantity ):
      config = config_list.pop( 0 )
      config.profile = profile
      config.hostname = 'mcp-auto--{0}-{1}-{2}'.format( job.pk, name, index )
      config.full_clean()
      config.save()
      results.append( config.pk )
      submitConfigureJob( config )

    return results

  @cinp.check_auth()
  @staticmethod
  def checkAuth( user, verb, id_list, action=None ):
    return True

  def __str__( self ):
    return 'Static Resource "{0}"'.format( self.description )


@cinp.model( not_allowed_verb_list=[ 'CREATE', 'DELETE', 'UPDATE', 'CALL' ] )
class NetworkResource( models.Model ):
  """
NetworkResource, name is the name of the SubNet/AddressBlock.  Really only used by DynamicResources
  """
  name = models.CharField( max_length=40, primary_key=True )
  preference = models.IntegerField( default=100 )  # the higher the number the greater the preference
  created = models.DateTimeField( editable=False, auto_now_add=True )
  updated = models.DateTimeField( editable=False, auto_now=True )

  def available( self, quantity ):
    contractor = getContractor()

    network = contractor.getNetworkUsage( self.name )
    if int( network[ 'total' ] ) - ( int( network[ 'static' ] ) + int( network[ 'dynamic' ] ) + int( network[ 'reserved' ] ) ) < quantity:
      return False

    return True

  @cinp.check_auth()
  @staticmethod
  def checkAuth( user, verb, id_list, action=None ):
    return True

  def __str__( self ):
    return 'Network Resource for network "{0}"'.format( self.name )
