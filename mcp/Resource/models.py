from django.core.exceptions import ValidationError
from django.db import models
from django.apps import apps

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
class BluePrint( models.Model ):
  """
BluePrint
  """
  name = models.CharField( max_length=40, primary_key=True )
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
    return 'BluePrint "{0}"'.format( self.name )


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

  def build( self ):
    self.subclass.build()

  def allocate( self, blueprint, config_values, hostname ):
    self.subclass.allocate( blueprint, config_values, hostname )

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
  interface_map = MapField()

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
    contractor.allocateStaticResource( self.contractor_structure_id, blueprint.name, config_values, hostname )
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

  # def _takeOver( self, instance, buildjob, name, index ):
  #   instance.buildjob = buildjob
  #   instance.name = name
  #   instance.index = index
  #   instance.hostname = 'mcp-auto--{0}-{1}-{2}'.format( buildjob.pk, name, index )
  #   instance.full_clean()
  #   instance.save()
  #
  #   contractor = getContractor()
  #   contractor.updateConfig( instance.structure_id, instance.config_values, instance.hostname )
  #
  # def _createNew( self, interface_map, buildjob, name, index ):
  #   Instance = apps.get_model( 'Processor', 'Instance' )
  #
  #   instance = Instance( resource=self )
  #   instance.interface_map = interface_map
  #   instance.buildjob = buildjob
  #   instance.name = name
  #   instance.index = index
  #   instance.hostname = 'mcp-auto--{0}-{1}-{2}'.format( buildjob.pk, name, index )
  #   instance.full_clean()
  #   instance.save()
  #
  #   instance.allocate()
  #
  # def _replentishPreAllocate( self ):
  #   quantity = self.build_ahead_count - self.buildjobresourceinstance_set.filter( buildjob__isnull=True ).count()
  #   if quantity < 1:
  #     return
  #
  #   network_id = _getAvailibleNetwork( self.site, quantity )
  #   if network_id is None:
  #     return
  #
  #   Instance = apps.get_model( 'Processor', 'Instance' )
  #   for _ in range( 0, quantity ):
  #     instance = Instance( resource=self )
  #     instance.interface_map = { 'eth0': { 'network': network_id, 'is_primary': True } }
  #     instance.hostname = 'mcp-preallocate--{0}-{1}'.format( self.name, instance.pk )
  #     instance.full_clean()
  #     instance.save()
  #
  #     instance.allocate()
  #     instance.build()

  def available( self, quantity, interface_map ):
    if not interface_map:  # for now is {} when empty would be nice if it was also None, this will cover both
      return _getAvailibleNetwork( self.site, quantity ) is not None

    return True

  # def allocate( self, job, name, quantity, interface_map ):
  #   if not interface_map:  # for now is {} when empty would be nice if it was also None, this will cover both
  #     interface_map = { 'eth0': { 'network': _getAvailibleNetwork( self.site, quantity ), 'is_primary': True } }
  #
  #     instance_list = self.buildjobresourceinstance_set.filter( buildjob__isnull=True ).order_by( 'pk' ).iterator()
  #
  #     for index in range( 0, quantity ):
  #       instance = next( instance_list, None )
  #       while instance is not None and instance.interface_map != interface_map:  # dicts don't allways sort the same way, so trying to query by interface_map will not work very well
  #         instance = next( instance_list, None )
  #
  #       if instance is not None:
  #         self._takeOver( instance, job, name, index )
  #       else:
  #         self._createNew( interface_map, job, name, index )
  #
  #       self._replentishPreAllocate()
  #
  #   else:
  #     for index in range( 0, quantity ):
  #       self._createNew( interface_map, job, name, index )

  def allocate( self, buildjob, buildresource, interface_map ):
    BuildJobResourceInstance = apps.get_model( 'Processor', 'BuildJobResourceInstance' )

    if not interface_map:  # for now is {} when empty would be nice if it was also None, this will cover both
      network = _getAvailibleNetwork( self.site, buildresource.quantity )
      interface_map = { 'eth0': { 'network_id': network.contractor_network_id, 'address_block_id': network.contractor_addressblock_id, 'is_primary': True } }

    for index in range( 0, buildresource.quantity ):
      resource_instance = DynamicResourceInstance( dynamic_resource=self )
      resource_instance.interface_map = interface_map
      resource_instance.full_clean()
      resource_instance.save()

      buildjob_resource = BuildJobResourceInstance( buildjob=buildjob, resource_instance=resource_instance )
      buildjob_resource.name = buildresource.name
      buildjob_resource.index = index
      buildjob_resource.blueprint = buildresource.blueprint
      buildjob_resource.full_clean()
      buildjob_resource.save()

      buildjob_resource.allocate()

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

  # def takeOver( self, config_values, hostname ):
  #   contractor = getContractor()
  #   contractor.updateDynamicResource( self.contractor_structure_id, config_values, hostname )

  def allocate( self, blueprint, config_values, hostname ):
    contractor = getContractor()
    self.contractor_foundation_id, self.contractor_structure_id = contractor.allocateDynamicResource( self.dynamic_resource.site.name, self.dynamic_resource.complex_id, blueprint.name, config_values, self.interface_map, hostname )
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
  name = models.CharField( max_length=50, primary_key=True )
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
