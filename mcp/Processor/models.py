from datetime import datetime

from django.utils.timezone import utc
from django.utils import simplejson
from django.db import models
from django.core.exceptions import ValidationError

from mcp.Projects.models import Build, Project, PackageVersion, Commit, RELEASE_TYPE_LENGTH, RELEASE_TYPE_CHOICES
from mcp.Resources.models import Resource, ResourceGroup
from plato.Config.lib import getSystemConfigValues

# techinically we sould be grouping all the same build to geather, but sence each package has a diffrent distro name in the version we end up
# with multiple "versions" for one "version" of the file.  So hopfully the rest of MCP maintains one commit at a time, and we will group
# all versions of a package togeather in the same Promotion for now, better logic is needed eventually
class Promotion( models.Model ):
  package_versions = models.ManyToManyField( PackageVersion, through='PromotionPkgVersion' )
  status = models.ManyToManyField( Build, through='PromotionBuild' )
  to_state = models.CharField( max_length=RELEASE_TYPE_LENGTH, choices=RELEASE_TYPE_CHOICES )
  created = models.DateTimeField( editable=False, auto_now_add=True )
  updated = models.DateTimeField( editable=False, auto_now=True )

  def __unicode__( self ):
    return 'Promotion for package/versions %s to "%s"' % ( [ ( '%s(%s)' % ( i.package.name, i.version ) ) for i in self.package_versions.all() ], self.to_state )

  def signalComplete( self, build ):
    promotion_build = self.promotionbuild_set.get( build=build )
    promotion_build.status = 'done'
    promotion_build.save()


class PromotionPkgVersion( models.Model ):
  promotion = models.ForeignKey( Promotion )
  package_version = models.ForeignKey( PackageVersion )
  packrat_id = models.CharField( max_length=100 )

  def __unicode__( self ):
    return 'PromotionPkgVersion for package "%s" version "%s" promoting to "%s"' % ( self.package_version.package.name, self.package_version.version, self.promotion.to_state )

  class Meta:
    unique_together = ( 'promotion', 'package_version' )


class PromotionBuild( models.Model ):
  promotion = models.ForeignKey( Promotion )
  build = models.ForeignKey( Build )
  status = models.CharField( max_length=50 )

  def __unicode__( self ):
    return 'PromotionBuild to state "%s" using build "%s" at "%s"' % ( self.promotion.to_state, self.build.name, self.status )

  class Meta:
    unique_together = ( 'promotion', 'build' )


class QueueItem( models.Model ):
  """
QueueItem
  """
  build = models.ForeignKey( Build )
  project = models.ForeignKey( Project )
  branch = models.CharField( max_length=50 )
  target = models.CharField( max_length=50 )
  requires = models.CharField( max_length=50 )
  priority = models.IntegerField( default=50 ) # higher the value, higer the priority
  manual = models.BooleanField() # if False, will not auto clean up, and will not block the project from updating/re-scaning for new jobs
  resource_status = models.TextField( default='{}' )
  resource_groups = models.ManyToManyField( ResourceGroup )
  commit = models.ForeignKey( Commit, null=True, blank=True, on_delete=models.SET_NULL )
  promotion = models.ForeignKey( Promotion, null=True, blank=True, on_delete=models.SET_NULL )
  created = models.DateTimeField( editable=False, auto_now_add=True )
  updated = models.DateTimeField( editable=False, auto_now=True )

  def checkResources( self ):
    result = {}
    for group in self.resource_groups.all():
      if not group.available():
        result[ group.name ] = 'Not Available'

    if result:
      return result

    resource_map = self.build.resources
    for name in resource_map:
      resource = resource_map[ name ][0].native
      quanitity = resource_map[ name ][1]
      tmp = resource.available( quanitity )
      if not tmp:
        result[ resource.name ] = 'Not Available'

    return result

  def allocateResources( self, job ): # warning, dosen't check first, make sure you are sure there are resources available before calling
    result = {}
    group_config_list = []
    for group in self.resource_groups.all():
      group_config_list += group.config_list

    resource_map = self.build.resources
    for name in resource_map:
      resource = resource_map[ name ][0].native
      quanitity = resource_map[ name ][1]
      config_list = resource.allocate( job, name, quanitity, config_id_list=group_config_list ) # first try to allocated from resource groups
      config_list += resource.allocate( job, name, quanitity - len( config_list ) ) # now allocated from general pool
      result[ name ] = []
      for config in config_list:
        result[ name ].append( { 'status': 'Allocated', 'config': config } )

    return result

  @staticmethod
  def inQueueBuild( build, branch, manual, priority, promotion=None ):
    item = QueueItem()
    item.build = build
    item.manual = manual
    item.project = build.project
    item.branch = branch
    item.target = build.name
    item.requires = '%s-requires' % build.name
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
    item.requires = '%s-requires' % target
    item.priority = priority
    item.commit = commit
    item.save()

    return item

  def save( self, *args, **kwargs ):
    try:
      simplejson.loads( self.resource_status )
    except ValueError:
      raise ValidationError( 'resource_status must be valid JSON' )

    super( QueueItem, self ).save( *args, **kwargs )

  def __unicode__( self ):
    return 'QueueItem for "%s" of priority "%s"' % ( self.build.name, self.priority )


class BuildJob( models.Model ):
  """
BuildJob
  """
  build = models.ForeignKey( Build, editable=False )
  project = models.ForeignKey( Project )
  branch = models.CharField( max_length=50 )
  target = models.CharField( max_length=50 )
  requires = models.CharField( max_length=50 )
  _resources = models.TextField( default='{}' )
  built_at = models.DateTimeField( editable=False, blank=True, null=True )
  ran_at = models.DateTimeField( editable=False, blank=True, null=True )
  reported_at = models.DateTimeField( editable=False, blank=True, null=True )
  released_at = models.DateTimeField( editable=False, blank=True, null=True )
  manual = models.BooleanField()
  commit = models.ForeignKey( Commit, null=True, blank=True, on_delete=models.SET_NULL )
  promotion = models.ForeignKey( Promotion, null=True, blank=True, on_delete=models.SET_NULL )
  created = models.DateTimeField( editable=False, auto_now_add=True )
  updated = models.DateTimeField( editable=False, auto_now=True )

  @property
  def resources( self ):
    return simplejson.loads( self._resources )

  @property
  def state( self ):
    if self.released_at and self.reported_at and self.ran_at and self.built_at:
      return 'released'

    if self.reported_at and self.ran_at and self.built_at:
      return 'reported'

    if self.ran_at and self.built_at:
      return 'ran'

    if self.built_at:
      return 'built'

    return 'new'

  @property
  def suceeded( self ):
    if self.ran_at is None:
      return None

    result = True
    for resource in self.resources:
      result &= self.resources[ 'result' ] is True

    return result

  def jobRan( self ):
    self.ran_at = datetime.utcnow().replace( tzinfo=utc )
    self.save()

  def updateResourceState( self, name, index, status ):
    tmp = simplejson.loads( self._resources )
    try:
      tmp[ name ][ index ][ 'status' ] = status
    except ( IndexError, KeyError ):
      return

    self._resources = simplejson.dumps( tmp )
    self.save()

  def setResourceSuccess( self, name, index, success ):
    tmp = simplejson.loads( self._resources )
    try:
      tmp[ name ][ index ][ 'success' ] = bool( success )
    except ( IndexError, KeyError ):
      return

    self._resources = simplejson.dumps( tmp )
    self.save()

  def setResourceResults( self, name, index, results ):
    tmp = simplejson.loads( self._resources )
    try:
      tmp[ name ][ index ][ 'results' ] = results
    except ( IndexError, KeyError ):
      return

    self._resources = simplejson.dumps( tmp )
    self.save()

  def getConfigStatus( self, name, index=None, count=None ):
    tmp = simplejson.loads( self._resources )
    config_list = tmp[ name ]
    if index:
      if count:
        config_list = tmp[ index:index + count ]
      else:
        config_list = tmp[ index: ]

    if index is None:
      index = 0

    results = {}
    for pos in range( 0, len( config_list ) ):
      results[ index + pos ] = Resource.config( config_list[ pos ][ 'config' ] ).status

    return results

  def getProvisioningInfo( self, name, index=None, count=None ):
    tmp = simplejson.loads( self._resources )
    config_list = tmp[ name ]
    if index:
      if count:
        config_list = tmp[ index:index + count ]
      else:
        config_list = tmp[ index: ]

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

  def save( self, *args, **kwargs ):
    try:
      simplejson.loads( self._resources )
    except ValueError:
      raise ValidationError( 'status must be valid JSON' )

    super( BuildJob, self ).save( *args, **kwargs )

  def __unicode__( self ):
    return 'BuildJob "%s" for build "%s"' % ( self.pk, self.build.name )

  class API:
    not_allowed_methods = ( 'CREATE', 'DELETE', 'UPDATE' )
    actions = {
                 'jobRan': [],
                 'updateResourceState': [ { 'type': 'String' }, { 'type': 'Integer' }, { 'type': 'String' } ],
                 'setResourceSuccess': [ { 'type': 'String' }, { 'type': 'Integer' }, { 'type': 'Boolean' } ],
                 'setResourceResults': [ { 'type': 'String' }, { 'type': 'Integer' }, { 'type': 'String' } ],
                 'getConfigStatus': [ { 'type': 'String' }, { 'type': 'Integer' }, { 'type': 'Integer' } ],
                 'getProvisioningInfo': [ { 'type': 'String' }, { 'type': 'Integer' }, { 'type': 'Integer' } ],
              }
