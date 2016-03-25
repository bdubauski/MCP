from datetime import datetime

from django.utils.timezone import utc
from django.utils import simplejson
from django.db import models
from django.core.exceptions import ValidationError

from mcp.Project.models import Build, Project, PackageVersion, Commit, RELEASE_TYPE_LENGTH, RELEASE_TYPE_CHOICES
from mcp.Resource.models import Resource, ResourceGroup, NetworkResource
from plato.Config.lib import getSystemConfigValues
from plato.Network.models import SubNet

# techinically we sould be grouping all the same build to geather, but sence each package has a diffrent distro name in the version we end up
# with multiple "versions" for one "version" of the file.  So hopfully the rest of MCP maintains one commit at a time, and we will group
# all versions of a package togeather in the same Promotion for now, better logic is needed eventually
class Promotion( models.Model ):
  package_versions = models.ManyToManyField( PackageVersion, through='PromotionPkgVersion', help_text='' )
  status = models.ManyToManyField( Build, through='PromotionBuild', help_text='' )
  to_state = models.CharField( max_length=RELEASE_TYPE_LENGTH, choices=RELEASE_TYPE_CHOICES )
  created = models.DateTimeField( editable=False, auto_now_add=True )
  updated = models.DateTimeField( editable=False, auto_now=True )

  def __unicode__( self ):
    return 'Promotion for package/versions %s to "%s"' % ( [ ( '%s(%s)' % ( i.package.name, i.version ) ) for i in self.package_versions.all() ], self.to_state )

  def signalComplete( self, build ):
    promotion_build = self.promotionbuild_set.get( build=build )
    promotion_build.status = 'done'
    promotion_build.save()

  class API:
    not_allowed_methods = ( 'CREATE', 'DELETE', 'UPDATE', 'CALL' )


class PromotionPkgVersion( models.Model ):
  promotion = models.ForeignKey( Promotion )
  package_version = models.ForeignKey( PackageVersion )
  packrat_id = models.CharField( max_length=100 )

  def __unicode__( self ):
    return 'PromotionPkgVersion for package "%s" version "%s" promoting to "%s"' % ( self.package_version.package.name, self.package_version.version, self.promotion.to_state )

  class Meta:
    unique_together = ( 'promotion', 'package_version' )

  class API:
    not_allowed_methods = ( 'CREATE', 'DELETE', 'UPDATE', 'CALL' )


class PromotionBuild( models.Model ):
  promotion = models.ForeignKey( Promotion )
  build = models.ForeignKey( Build )
  status = models.CharField( max_length=50 )

  def __unicode__( self ):
    return 'PromotionBuild to state "%s" using build "%s" at "%s"' % ( self.promotion.to_state, self.build.name, self.status )

  class Meta:
    unique_together = ( 'promotion', 'build' )

  class API:
    not_allowed_methods = ( 'CREATE', 'DELETE', 'UPDATE', 'CALL' )


class QueueItem( models.Model ):
  """
QueueItem
  """
  build = models.ForeignKey( Build )
  project = models.ForeignKey( Project )
  branch = models.CharField( max_length=50 )
  target = models.CharField( max_length=50 )
  priority = models.IntegerField( default=50 ) # higher the value, higer the priority
  manual = models.BooleanField() # if False, will not auto clean up, and will not block the project from updating/re-scaning for new jobs
  resource_status = models.TextField( default='{}' )
  resource_groups = models.ManyToManyField( ResourceGroup, help_text='' )
  commit = models.ForeignKey( Commit, null=True, blank=True, on_delete=models.SET_NULL )
  promotion = models.ForeignKey( Promotion, null=True, blank=True, on_delete=models.SET_NULL )
  created = models.DateTimeField( editable=False, auto_now_add=True )
  updated = models.DateTimeField( editable=False, auto_now=True )

  def checkResources( self ):
    compute = {}
    network = {}
    for group in self.resource_groups.all():
      if not group.available():
        compute[ group.name ] = 'Not Available'

    if compute:
      return compute, network

    for buildresource in self.build.buildresource_set.all():
      quanity = buildresource.quanity
      resource = buildresource.resource.native
      tmp = resource.available( quanity )
      if not tmp:
        compute[ resource.name ] = 'Not Available'

    have = len( NetworkResource.objects.filter( buildjob=None ) )
    need = len( simplejson.loads( self.build.networks ) )
    if have < need:
      network[ 'network' ] = 'Need: %s   Available: %s' % ( need, have )

    return ( compute, network )

  def allocateResources( self, job ): # warning, dosen't check first, make sure you are sure there are resources available before calling
    compute = {}
    network = {}
    group_config_list = []
    for group in self.resource_groups.all():
      group_config_list += group.config_list

    for buildresource in self.build.buildresource_set.all():
      name = buildresource.name
      quanity = buildresource.quanity
      resource = buildresource.resource.native
      if group_config_list: # should we have an option that prevents from allocating from outside the group_config_list?
        config_list = resource.allocate( job, name, quanity, config_id_list=group_config_list ) # first try to allocated from resource groups
      config_list += resource.allocate( job, name, quanity - len( config_list ) ) # now allocated from general pool
      compute[ name ] = []
      for config in config_list:
        compute[ name ].append( { 'status': 'Allocated', 'config': config } )

    networks = simplejson.loads( self.build.networks )
    resource_list = list( NetworkResource.objects.filter( buildjob=None ) )
    for name in networks:
      network[ name ] = resource_list.pop( 0 )

    return ( compute, network )

  @staticmethod
  def inQueueBuild( build, branch, manual, priority, promotion=None ):
    item = QueueItem()
    item.build = build
    item.manual = manual
    item.project = build.project
    item.branch = branch
    item.target = build.name
    item.priority = priority
    item.promotion = promotion
    item.save()

    return item

  @staticmethod
  def inQueueTarget( project, branch, manual, distro, target, priority, commit=None ):
    try:
      build = Build.objects.get( project_id='_builtin_', name=distro )
    except Build.DoesNotExist:
      raise Exception( 'distro "%s" not set up' % distro )

    item = QueueItem()
    item.build = build
    item.manual = manual
    item.project = project
    item.branch = branch
    item.target = target
    item.priority = priority
    item.commit = commit
    item.save()

    return item

  @staticmethod
  def queue( build ):
    QueueItem.inQueueBuild( build, 'master', True, 100 )

  def save( self, *args, **kwargs ):
    try:
      simplejson.loads( self.resource_status )
    except ValueError:
      raise ValidationError( 'resource_status must be valid JSON' )

    super( QueueItem, self ).save( *args, **kwargs )

  def __unicode__( self ):
    return 'QueueItem for "%s" of priority "%s"' % ( self.build.name, self.priority )

  class API:
    not_allowed_methods = ( 'CREATE', 'DELETE', 'UPDATE', 'CALL' )
    list_filters = { 'project': { 'project': Project } }
    actions = {
                'queue': [ { 'type': 'Model', 'model': Build } ],
              }

    @staticmethod
    def buildQS( qs, filter, values ):
      if filter == 'project':
        return qs.filter( project=values[ 'project' ] )

      raise Exception( 'Invalid filter "%s"' % filter )

class BuildJob( models.Model ):
  """
BuildJob
  """
  STATE_LIST = ( 'new', 'build', 'ran', 'reported', 'acknowledged', 'released' )
  build = models.ForeignKey( Build, editable=False )
  project = models.ForeignKey( Project )
  branch = models.CharField( max_length=50 )
  target = models.CharField( max_length=50 )
  resources = models.TextField( default='{}' )
  built_at = models.DateTimeField( editable=False, blank=True, null=True )
  ran_at = models.DateTimeField( editable=False, blank=True, null=True )
  reported_at = models.DateTimeField( editable=False, blank=True, null=True )
  acknowledged_at = models.DateTimeField( editable=False, blank=True, null=True )
  released_at = models.DateTimeField( editable=False, blank=True, null=True )
  manual = models.BooleanField()
  commit = models.ForeignKey( Commit, null=True, blank=True, on_delete=models.SET_NULL )
  promotion = models.ForeignKey( Promotion, null=True, blank=True, on_delete=models.SET_NULL )
  networks = models.ManyToManyField( NetworkResource, through='BuildJobNetworkResource', help_text='' )
  created = models.DateTimeField( editable=False, auto_now_add=True )
  updated = models.DateTimeField( editable=False, auto_now=True )

  @property
  def state( self ):
    if self.released_at and self.acknowledged_at and self.reported_at and self.ran_at and self.built_at:
      return 'released'

    if self.acknowledged_at and self.reported_at and self.ran_at and self.built_at:
      return 'acknowledged'

    if self.reported_at and self.ran_at and self.built_at:
      return 'reported'

    if self.ran_at and self.built_at:
      return 'ran'

    if self.built_at:
      return 'built'

    return 'new'

  # some jobs have more than one resources, in this case, if a resource hasn't
  # report a status we will assume it has sucess, due to the fact that many
  # of the sub resources will never report
  @property
  def suceeded( self ):
    if self.ran_at is None:
      return None

    result = True
    resource_map = simplejson.loads( self.resources )
    for target in resource_map:
      for i in range( 0, len( resource_map[ target ] ) ):
        result &= resource_map[ target ][ i ].get( 'success', True )

    return result

  def jobRan( self ):
    if not self.built_at:
      self.built_at = datetime.utcnow().replace( tzinfo=utc )

    self.ran_at = datetime.utcnow().replace( tzinfo=utc )
    self.save()

  def acknowledge( self ):
    if self.reported_at is None:
      raise ValidationError( 'Can not Acknoledge un-reported jobs' )

    self.acknowledged_at = datetime.utcnow().replace( tzinfo=utc )
    self.save()

  def updateResourceState( self, name, index, status ):
    resource_map = simplejson.loads( self.resources )
    try:
      resource_map[ name ][ index ][ 'status' ] = status
    except ( IndexError, KeyError ):
      return

    self.resources = simplejson.dumps( resource_map )
    self.save()

  def setResourceSuccess( self, name, index, success ):
    resource_map = simplejson.loads( self.resources )
    try:
      resource_map[ name ][ index ][ 'success' ] = bool( success )
    except ( IndexError, KeyError ):
      return

    self.resources = simplejson.dumps( resource_map )
    self.save()

  def setResourceResults( self, name, index, results ):
    resource_map = simplejson.loads( self.resources )
    try:
      resource_map[ name ][ index ][ 'results' ] = results
    except ( IndexError, KeyError ):
      return

    self.resources = simplejson.dumps( resource_map )
    self.save()

  def getConfigStatus( self, name, index=None, count=None ):
    resource_map = simplejson.loads( self.resources )
    try:
      config_list = resource_map[ name ]
    except KeyError:
      return {}

    if index is not None:
      if count is not None:
        config_list = config_list[ index:index + count ]
      else:
        config_list = config_list[ index: ]

    if index is None:
      index = 0

    results = {}
    for pos in range( 0, len( config_list ) ):
      results[ index + pos ] = Resource.config( config_list[ pos ][ 'config' ] ).status

    return results

  def getProvisioningInfo( self, name, index=None, count=None ):
    resource_map = simplejson.loads( self.resources )
    try:
      config_list = resource_map[ name ]
    except KeyError:
      return {}

    if index is not None:
      if count is not None:
        config_list = config_list[ index:index + count ]
      else:
        config_list = config_list[ index: ]

    if index is None:
      index = 0

    results = {}
    for pos in range( 0, len( config_list ) ):
      config = Resource.config( config_list[ pos ][ 'config' ] )
      values = getSystemConfigValues( config=config, profile=config.profile )
      values[ 'system_serial_number' ] = config.target.system_serial_number
      values[ 'chassis_serial_number' ] = config.target.chassis_serial_number
      values[ 'config_values' ] = config.config_values
      values[ 'timestamp' ] = values[ 'timestamp' ].strftime( '%Y-%m-%d %H:%M:%S' )
      results[ index + pos ] = values

    return results

  def setConfigValues( self, values, name, index=None, count=None ):
    resource_map = simplejson.loads( self.resources )
    try:
      config_list = resource_map[ name ]
    except KeyError:
      return False

    if index is not None:
      if count is not None:
        config_list = config_list[ index:index + count ]
      else:
        config_list = config_list[ index: ]

    for pos in range( 0, len( config_list ) ):
      config = Resource.config( config_list[ pos ][ 'config' ] )
      new_values = simplejson.loads( config.config_values )
      new_values.update( values )
      config.config_values = simplejson.dumps( new_values )
      config.save()

    return True

  def getNetworkInfo( self, name ):
    try:
      network = self.buildjobnetworkresource_set.get( name=name )
    except BuildJobNetworkResource.DoesNotExist:
      return {}

    try:
      subnet = SubNet.objects.get( pk=network.networkresource.subnet )
    except ( SubNet.DoesNotExist, NetworkResource.DoesNotExist ):
      return {}

    results = { 'description': network.name, 'network': subnet.network, 'prefix': subnet.prefix }
    if subnet.gateway:
      results[ 'gateway' ] = subnet.gateway
    if subnet.broadcast:
      results[ 'broadcast' ] = subnet.broadcast
    if subnet.vlan:
      results[ 'vlan' ] = subnet.vlan

    return results

  def save( self, *args, **kwargs ):
    try:
      simplejson.loads( self.resources )
    except ValueError:
      raise ValidationError( 'status must be valid JSON' )

    super( BuildJob, self ).save( *args, **kwargs )

  def __unicode__( self ):
    return 'BuildJob "%s" for build "%s"' % ( self.pk, self.build.name )

  class API:
    not_allowed_methods = ( 'CREATE', 'DELETE', 'UPDATE' )
    actions = {  # TODO: these can only be called by jobs, need some kind of auth for them
                 'jobRan': [],
                 'updateResourceState': [ { 'type': 'String' }, { 'type': 'Integer' }, { 'type': 'String' } ],
                 'setResourceSuccess': [ { 'type': 'String' }, { 'type': 'Integer' }, { 'type': 'Boolean' } ],
                 'setResourceResults': [ { 'type': 'String' }, { 'type': 'Integer' }, { 'type': 'String' } ],
                 'getConfigStatus': [ { 'type': 'String' }, { 'type': 'Integer' }, { 'type': 'Integer' } ],
                 'getProvisioningInfo': [ { 'type': 'String' }, { 'type': 'Integer' }, { 'type': 'Integer' } ], # called by UI
                 'setConfigValues': [ { 'type': 'Map' }, { 'type': 'String' }, { 'type': 'Integer' }, { 'type': 'Integer' } ],
                 'getNetworkInfo': [ { 'type': 'String' } ],
                 # these are normal
                 'acknowledge': []
              }
    constants = ( 'STATE_LIST', )
    properties = ( 'state', 'suceeded' )
    list_filters = { 'project': { 'project': Project } }

    @staticmethod
    def buildQS( qs, filter, values ):
      if filter == 'project':
        return qs.filter( project=values[ 'project' ] )

      raise Exception( 'Invalid filter "%s"' % filter )


class BuildJobNetworkResource( models.Model ):
  buildjob = models.ForeignKey( BuildJob )
  networkresource = models.ForeignKey( NetworkResource )
  name = models.CharField( max_length=100 )

  def __unicode__( self ):
    return 'BuildJobNetworkResource for BuildJob "%s" NetworkResource "%s" Named "%s"' % ( self.buildjob, self.networkresource, self.name )

  class Meta:
    unique_together = ( ( 'buildjob', 'networkresource' ), ( 'buildjob', 'name' ) )
