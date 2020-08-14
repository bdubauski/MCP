from django.core.exceptions import ValidationError
from django.db import models
from django.apps import apps
from django.conf import settings

from cinp.orm_django import DjangoCInP as CInP

from mcp.lib.t3kton import getContractor
from mcp.fields import MapField, name_regex

# NOTE: these are not "thread safe", there is no per-instance resource reservation
# make sure only one thing is calling these methods at a time...


cinp = CInP( 'Resource', '0.1' )


def _getAvailibleNetwork( site, quantity ):
  for network in site.network_set.filter( monalythic=False ):
    if network.available( quantity ):
      return network

  return None


@cinp.model( not_allowed_verb_list=[ 'CREATE', 'DELETE', 'UPDATE', 'CALL' ] )
class Site( models.Model ):
  """
Site
  """
  name = models.CharField( max_length=40, primary_key=True )  # also the site_id on contractor
  created = models.DateTimeField( editable=False, auto_now_add=True )
  updated = models.DateTimeField( editable=False, auto_now=True )

  def clean( self, *args, **kwargs ):
    super().clean( *args, **kwargs )
    errors = {}

    if not name_regex.match( self.name ):  # should we also ping contractor?
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
  key = models.CharField( max_length=250, editable=False, primary_key=True )  # until django supports multi filed primary keys
  site = models.ForeignKey( Site, on_delete=models.CASCADE )
  name = models.CharField( max_length=50 )
  description = models.CharField( max_length=100 )
  created = models.DateTimeField( editable=False, auto_now_add=True )
  updated = models.DateTimeField( editable=False, auto_now=True )

  def available( self, quantity, interface_map ):
    return False

  def allocate( job, buildresource, interface_map ):
    raise Exception( 'can not allocate a Base level Resource' )

  @property
  def subclass( self ):
    try:
      return self.dynamicresource
    except AttributeError:
      pass

    try:
      return self.staticresource
    except AttributeError:
      pass

    return self

  @cinp.check_auth()
  @staticmethod
  def checkAuth( user, verb, id_list, action=None ):
    return True

  def clean( self, *args, **kwargs ):
    super().clean( *args, **kwargs )
    self.key = '{0}_{1}'.format( self.site.name, self.name )

    errors = {}

    if errors:
      raise ValidationError( errors )

  def __str__( self ):
    return 'Resource "{0}"'.format( self.name )

  class Meta:
    unique_together = ( 'name', 'site' )


@cinp.model( not_allowed_verb_list=[ 'CREATE', 'DELETE', 'UPDATE', 'CALL' ] )
class ResourceInstance( models.Model ):
  contractor_structure_id = models.IntegerField( unique=True, blank=True, null=True )
  created = models.DateTimeField( editable=False, auto_now_add=True )
  updated = models.DateTimeField( editable=False, auto_now=True )

  @property
  def subclass( self ):
    try:
      return self.dynamicresourceinstance
    except AttributeError:
      pass

    try:
      return self.staticresourceinstance
    except AttributeError:
      pass

    raise Exception( 'ResourceInstance subclass missing' )

  @property
  def resource( self ):
    return self.subclass.resource()

  def allocate( self, blueprint, config_values, hostname ):
    self.subclass.allocate( blueprint, config_values, hostname )

  def updateConfig( self, config_values, hostname ):
    contractor = getContractor()
    contractor.updateConfig( self.contractor_structure_id, config_values, hostname )

  def build( self ):
    self.subclass.build()

  def release( self ):
    self.subclass.release()

  def cleanup( self ):
    self.subclass.cleanup()

  def __str__( self ):
    return 'ResourceInstance'


@cinp.model( not_allowed_verb_list=[ 'CREATE', 'DELETE', 'UPDATE', 'CALL' ] )
class StaticResource( Resource ):
  """
StaticResource
  """
  group_name = models.CharField( max_length=50 )
  interface_map = MapField( blank=True )

  def available( self, quantity, interface_map ):
    for name in interface_map.keys():
      try:  # we only care if the interfaces named in the config match the resource, extra interfaces on the resource are fine
        if interface_map[ name ][ 'network' ] != self.interface_map[ name ][ 'network' ]:
          return False
      except KeyError:
        return False

    return self.staticresourceinstance_set.filter( buildjob__isnull=True ).count() >= quantity

  def allocate( job, buildresource, interface_map ):
    pass

  @cinp.check_auth()
  @staticmethod
  def checkAuth( user, verb, id_list, action=None ):
    return True

  def __str__( self ):
    return 'StaticResource "{0}"'.format( self.name )


@cinp.model( not_allowed_verb_list=[ 'CREATE', 'DELETE', 'UPDATE', 'CALL' ] )
class StaticResourceInstance( ResourceInstance ):
  """
StaticResourceInstance
  """
  static_resource = models.ForeignKey( StaticResource, on_delete=models.CASCADE )

  @property
  def resource( self ):
    return self.static_resource

  def allocate( self, blueprint, config_values, hostname ):
    contractor = getContractor()
    contractor.allocateStaticResource( self.contractor_structure_id, blueprint, config_values, hostname )
    contractor.registerWebHook( self.buildjobresourceinstance, True, structure_id=self.contractor_structure_id )

  def build( self ):
    contractor = getContractor()
    contractor.builStaticResource( self.contractor_structure_id )
    contractor.registerWebHook( self.buildjobresourceinstance, True, structure_id=self.contractor_structure_id )

  def release( self ):
    contractor = getContractor()
    contractor.releaseStatic( self.contractor_structure_id )
    contractor.registerWebHook( self.buildjobresourceinstance, False, structure_id=self.contractor_structure_id )

  def cleanup( self ):
    pass

  @cinp.check_auth()
  @staticmethod
  def checkAuth( user, verb, id_list, action=None ):
    return True

  def __str__( self ):
    return 'StaticResourceInstance for "{0}" contractor id: "{1}"'.format( self.static_resource, self.contractor_id )


@cinp.model( not_allowed_verb_list=[ 'CREATE', 'DELETE', 'UPDATE', 'CALL' ] )
class DynamicResource( Resource ):
  """
DynamicResource
  """
  # build_ahead_count = models.IntegerField( default=0 )
  complex_id = models.CharField( max_length=40 )  # should match contractor complex name/pk

  def _takeOver( self, dynamic_resource_instance, buildjob, buildresource, index ):
    buildjob_resource = dynamic_resource_instance.buildjobresourceinstance
    buildjob_resource.buildjob = buildjob
    buildjob_resource.name = buildresource.name
    buildjob_resource.index = index
    buildjob_resource.config_values = buildresource.config_values
    buildjob_resource.autorun = buildresource.autorun
    buildjob_resource.full_clean()
    buildjob_resource.save()

    buildjob_resource.updateConfig()

    if buildjob_resource.state == 'built':  # there may be some triggers(autorun) that would of happened if this was built normally, do that now
      buildjob_resource.signal_built( buildjob_resource.cookie )

  def _createNew( self, interface_map, buildjob, buildresource, index ):
    BuildJobResourceInstance = apps.get_model( 'Processor', 'BuildJobResourceInstance' )

    resource_instance = DynamicResourceInstance( dynamic_resource=self )
    resource_instance.interface_map = interface_map
    resource_instance.full_clean()
    resource_instance.save()

    buildjob_resource = BuildJobResourceInstance( buildjob=buildjob, resource_instance=resource_instance )
    buildjob_resource.name = buildresource.name
    buildjob_resource.index = index
    buildjob_resource.blueprint = buildresource.blueprint
    buildjob_resource.config_values = buildresource.config_values
    buildjob_resource.autorun = buildresource.autorun
    buildjob_resource.full_clean()
    buildjob_resource.save()

    buildjob_resource.allocate()

  def _replenish( self, interface_map, blueprint, build_ahead_count ):
    BuildJobResourceInstance = apps.get_model( 'Processor', 'BuildJobResourceInstance' )

    quantity = build_ahead_count - DynamicResourceInstance.objects.filter( buildjobresourceinstance__buildjob__isnull=True, buildjobresourceinstance__blueprint=blueprint, dynamic_resource=self ).count()
    if quantity < 1:
      return

    for _ in range( 0, quantity ):
      resource_instance = DynamicResourceInstance( dynamic_resource=self )
      resource_instance.interface_map = interface_map
      resource_instance.full_clean()
      resource_instance.save()

      buildjob_resource = BuildJobResourceInstance( resource_instance=resource_instance )
      buildjob_resource.name = 'prallocate'
      buildjob_resource.index = 0
      buildjob_resource.blueprint = blueprint
      buildjob_resource.full_clean()
      buildjob_resource.save()

      buildjob_resource.allocate()
      buildjob_resource.build()

  def available( self, quantity, interface_map ):
    if not interface_map:  # for now is {} when empty would be nice if it was also None, this will cover both
      return _getAvailibleNetwork( self.site, quantity ) is not None

    return True

  def allocate( self, buildjob, buildresource, interface_map ):
    use_prealloc = interface_map or buildresource.config_values  # no preallocation for non-default networks, and custom config might have values to tweek the build ie: cpu count

    if not interface_map:
      network = _getAvailibleNetwork( self.site, buildresource.quantity )  # yes, if we are getting only pre-allocated stuff, we are double counting the network ips, however we need ips for the new resources that are going to backfill
      interface_map = { 'eth0': { 'network_id': network.contractor_network_id, 'address_block_id': network.contractor_addressblock_id, 'is_primary': True } }

    if use_prealloc:
      for index in range( 0, buildresource.quantity ):
        self._createNew( interface_map, buildjob, buildresource, index )

      return

    dynamic_resource_instance_list = DynamicResourceInstance.objects.filter( buildjobresourceinstance__buildjob__isnull=True, buildjobresourceinstance__blueprint=buildresource.blueprint, dynamic_resource=self ).order_by( 'pk' ).iterator()

    for index in range( 0, buildresource.quantity ):
      dynamic_resource_instance = next( dynamic_resource_instance_list, None )
      if dynamic_resource_instance is not None:
        self._takeOver( dynamic_resource_instance, buildjob, buildresource, index )
      else:
        self._createNew( interface_map, buildjob, buildresource, index )

    self._replenish( interface_map, buildresource.blueprint, settings.BUILD_AHEAD_COUNT.get( buildresource.blueprint, 0 ) )

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
    return 'Resource "{0}"({1})'.format( self.description, self.name )


@cinp.model( not_allowed_verb_list=[ 'CREATE', 'DELETE', 'UPDATE' ] )
class DynamicResourceInstance( ResourceInstance ):
  """
DynamicResourceInstance
  """
  dynamic_resource = models.ForeignKey( DynamicResource, on_delete=models.PROTECT )  # this is protected so we don't leave VMs laying arround
  contractor_foundation_id = models.CharField( max_length=100, blank=True, null=True )  # should match foundation locator
  interface_map = MapField()

  @property
  def resource( self ):
    return self.dynamic_resource

  def allocate( self, blueprint, config_values, hostname ):
    contractor = getContractor()
    self.contractor_foundation_id, self.contractor_structure_id = contractor.allocateDynamicResource( self.dynamic_resource.site.name, self.dynamic_resource.complex_id, blueprint, config_values, self.interface_map, hostname )
    self.full_clean()
    self.save()

  def build( self ):
    contractor = getContractor()
    contractor.buildDynamicResource( self.contractor_foundation_id, self.contractor_structure_id )
    contractor.registerWebHook( self.buildjobresourceinstance, True, structure_id=self.contractor_structure_id )

  def release( self ):
    contractor = getContractor()
    if contractor.releaseDynamicResource( self.contractor_foundation_id, self.contractor_structure_id ):
      contractor.registerWebHook( self.buildjobresourceinstance, False, foundation_id=self.contractor_foundation_id )

  def cleanup( self ):
    contractor = getContractor()
    contractor.deleteDynamicResource( self.contractor_foundation_id, self.contractor_structure_id )
    self.delete()

  @cinp.check_auth()
  @staticmethod
  def checkAuth( user, verb, id_list, action=None ):
    return True

  def __str__( self ):
    return 'DynamicResourceInstance for "{0}" contractor id: "{1}"'.format( self.dynamic_resource, self.contractor_structure_id )


@cinp.model( not_allowed_verb_list=[ 'CREATE', 'DELETE', 'UPDATE', 'CALL' ] )
class Network( models.Model ):
  """
Network, name is the name of the SubNet/AddressBlock.
  """
  name = models.CharField( max_length=82, primary_key=True )  # both addressblock and network names are 40, plus a little to spare
  site = models.ForeignKey( Site, on_delete=models.CASCADE )
  contractor_addressblock_id = models.IntegerField( unique=True )  # unique b/c we don't have anything to check for overlap between networks, thus avoiding over subscription of the ip addresses
  contractor_network_id = models.IntegerField()
  monalythic = models.BooleanField( default=True )  # only use for one build at a time, also use for sub-let builds, ie: we are not going to ask contractor about it.
  size = models.IntegerField()
  created = models.DateTimeField( editable=False, auto_now_add=True )
  updated = models.DateTimeField( editable=False, auto_now=True )

  def available( self, quantity ):  # TODO: rethink, mabey it should be a class method, and probably should return the resources, merge with allocate?
    if self.monalythic:
      return self.build_set.all().count() == 0

    contractor = getContractor()

    network = contractor.getNetworkUsage( self.contractor_addressblock_id )
    if int( network[ 'total' ] ) - ( int( network[ 'static' ] ) + int( network[ 'dynamic' ] ) + int( network[ 'reserved' ] ) ) < quantity:
      return False

    return True

  @cinp.check_auth()
  @staticmethod
  def checkAuth( user, verb, id_list, action=None ):
    return True

  def __str__( self ):
    return 'Network Resource for network "{0}"'.format( self.name )
