import uuid
from datetime import datetime, timezone

from django.db import models
from django.core.exceptions import ValidationError, PermissionDenied

from cinp.orm_django import DjangoCInP as CInP

from mcp.fields import MapField, StringListField

from mcp.Project.models import Build, Project, PackageVersion, Commit, RELEASE_TYPE_LENGTH, RELEASE_TYPE_CHOICES
from mcp.Resource.models import Resource, NetworkResource, Site
from mcp.User.models import User


cinp = CInP( 'Processor', '0.1' )


BUILDJOB_STATE_LIST = ( 'new', 'build', 'ran', 'reported', 'acknowledged', 'released' )


# techinically we sould be grouping all the same build to geather, but sence each package has a diffrent distro name in the version we end up
# with multiple "versions" for one "version" of the file.  So hopfully the rest of MCP maintains one commit at a time, and we will group
# all versions of a package togeather in the same Promotion for now, better logic is needed eventually
@cinp.model( not_allowed_verb_list=[ 'CREATE', 'DELETE', 'UPDATE', 'CALL' ] )
class Promotion( models.Model ):
  package_versions = models.ManyToManyField( PackageVersion, through='PromotionPkgVersion', help_text='' )
  status = models.ManyToManyField( Build, through='PromotionBuild', help_text='' )
  to_state = models.CharField( max_length=RELEASE_TYPE_LENGTH, choices=RELEASE_TYPE_CHOICES )
  created = models.DateTimeField( editable=False, auto_now_add=True )
  updated = models.DateTimeField( editable=False, auto_now=True )

  def signalComplete( self, build ):
    promotion_build = self.promotionbuild_set.get( build=build )
    promotion_build.status = 'done'
    promotion_build.full_clean()
    promotion_build.save()

  @cinp.check_auth()
  @staticmethod
  def checkAuth( user, verb, id_list, action=None ):
    return True

  def __str__( self ):
    return 'Promotion for package/versions {0} to "{1}"'.format( [ ( '{0}({1})'.format( i.package.name, i.version ) ) for i in self.package_versions.all() ], self.to_state )


@cinp.model( not_allowed_verb_list=[ 'CREATE', 'DELETE', 'UPDATE', 'CALL' ] )
class PromotionPkgVersion( models.Model ):
  promotion = models.ForeignKey( Promotion, on_delete=models.CASCADE )
  package_version = models.ForeignKey( PackageVersion, on_delete=models.CASCADE )
  packrat_id = models.CharField( max_length=100 )

  @cinp.check_auth()
  @staticmethod
  def checkAuth( user, verb, id_list, action=None ):
    return True

  def __str__( self ):
    return 'PromotionPkgVersion for package "{0}" version "{1}" promoting to "{2}"'.format( self.package_version.package.name, self.package_version.version, self.promotion.to_state )

  class Meta:
    unique_together = ( 'promotion', 'package_version' )


@cinp.model( not_allowed_verb_list=[ 'CREATE', 'DELETE', 'UPDATE', 'CALL' ] )
class PromotionBuild( models.Model ):
  promotion = models.ForeignKey( Promotion, on_delete=models.CASCADE )
  build = models.ForeignKey( Build, on_delete=models.CASCADE )
  status = models.CharField( max_length=50 )

  @cinp.check_auth()
  @staticmethod
  def checkAuth( user, verb, id_list, action=None ):
    return True

  def __str__( self ):
    return 'PromotionBuild to state "{0}" using build "{1}" at "{2}"'.format( self.promotion.to_state, self.build.name, self.status )

  class Meta:
    unique_together = ( 'promotion', 'build' )


@cinp.model( not_allowed_verb_list=[ 'CREATE', 'DELETE', 'UPDATE', 'CALL' ] )
class QueueItem( models.Model ):
  """
QueueItem
  """
  build = models.ForeignKey( Build, on_delete=models.CASCADE, editable=False )
  project = models.ForeignKey( Project, on_delete=models.CASCADE, editable=False )
  branch = models.CharField( max_length=50 )
  target = models.CharField( max_length=50 )
  priority = models.IntegerField( default=50 )  # higher the value, higer the priority
  manual = models.BooleanField()  # if False, will not auto clean up, and will not block the project from updating/re-scaning for new jobs
  user = models.ForeignKey( User, null=True, blank=True, on_delete=models.SET_NULL )
  resource_status_map = MapField( blank=True )
  commit = models.ForeignKey( Commit, null=True, blank=True, on_delete=models.SET_NULL )
  promotion = models.ForeignKey( Promotion, null=True, blank=True, on_delete=models.SET_NULL )
  created = models.DateTimeField( editable=False, auto_now_add=True )
  updated = models.DateTimeField( editable=False, auto_now=True )

  def checkResources( self ):
    compute = {}
    network = {}
    total_ips = 0

    for buildresource in self.build.buildresource_set.all():
      quanity = buildresource.quanity
      resource = buildresource.resource.subclass
      tmp = resource.available( quanity )
      if not tmp:
        compute[ resource.name ] = 'Not Available'

      total_ips += quanity

    target_network = None
    for resource in NetworkResource.objects.all().order_by( '-preference' ):
      if resource.available( total_ips ):
        target_network = resource
        break

    if target_network is None:
      network[ 'network' ] = 'Need: {0}'.format( total_ips )

    return ( compute, network, target_network )

  def allocateResources( self, job, target_network ):  # warning, this dosen't check first, make sure you are sure there are resources available before calling
    compute = {}
    network = {}

    resource_list = list( NetworkResource.objects.all() )
    for name in self.build.network_map:
      network[ name ] = resource_list.pop( 0 )

    for buildresource in self.build.buildresource_set.all():
      name = buildresource.name
      quanity = buildresource.quanity
      resource = buildresource.resource.subclass
      config_list = []
      config_list = resource.allocate( job, name, quanity - len( config_list ), target_network )
      compute[ name ] = []
      for config in config_list:
        compute[ name ].append( { 'status': 'Allocated', 'config': config } )

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
    item.full_clean()
    item.save()

    return item

  @staticmethod
  def inQueueTarget( project, branch, manual, distro, target, priority, commit=None ):
    try:
      build = Build.objects.get( project_id='_builtin_', name=distro )
    except Build.DoesNotExist:
      raise Exception( 'distro "{0}" not set up'.format( distro ) )

    item = QueueItem()
    item.build = build
    item.manual = manual
    item.project = project
    item.branch = branch
    item.target = target
    item.priority = priority
    item.commit = commit
    item.full_clean()
    item.save()

    return item

  @cinp.action( return_type='Integer', paramater_type_list=[ { 'type': '_USER_' }, { 'type': 'Model', 'model': Build } ] )
  @staticmethod
  def queue( user, build ):
    if not user.has_perm( 'Processor.can_build' ):
      raise PermissionDenied()

    item = QueueItem.inQueueBuild( build, 'master', True, 100 )
    return item.pk

  @cinp.list_filter( name='project', paramater_type_list=[ { 'type': 'Model', 'model': Project } ] )
  @staticmethod
  def filter_project( project ):
    return QueueItem.objects.filter( project=project )

  @cinp.check_auth()
  @staticmethod
  def checkAuth( user, verb, id_list, action=None ):
    return True

  def clean( self, *args, **kwargs ):
    super().clean( *args, **kwargs )
    errors = {}

    if errors:
      raise ValidationError( errors )

  def __str__( self ):
    return 'QueueItem for "{0}" of priority "{1}"'.format( self.build.name, self.priority )


@cinp.model( not_allowed_verb_list=[ 'CREATE', 'DELETE', 'UPDATE' ], property_list=[ { 'name': 'state', 'choices': BUILDJOB_STATE_LIST }, 'suceeded', 'score' ] )
class BuildJob( models.Model ):
  """
BuildJob
  """
  build = models.ForeignKey( Build, on_delete=models.PROTECT, editable=False )  # don't delete Builds/projects when things are in flight
  project = models.ForeignKey( Project, on_delete=models.PROTECT, editable=False )
  branch = models.CharField( max_length=50 )
  target = models.CharField( max_length=50 )
  built_at = models.DateTimeField( editable=False, blank=True, null=True )
  ran_at = models.DateTimeField( editable=False, blank=True, null=True )
  reported_at = models.DateTimeField( editable=False, blank=True, null=True )
  acknowledged_at = models.DateTimeField( editable=False, blank=True, null=True )
  released_at = models.DateTimeField( editable=False, blank=True, null=True )
  manual = models.BooleanField()
  user = models.ForeignKey( User, null=True, blank=True, on_delete=models.SET_NULL )
  commit = models.ForeignKey( Commit, null=True, blank=True, on_delete=models.SET_NULL )
  promotion = models.ForeignKey( Promotion, null=True, blank=True, on_delete=models.SET_NULL )
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
    for target in self.resource_map:
      for i in range( 0, len( self.resource_map[ target ] ) ):
        result &= self.resource_map[ target ][ i ].get( 'success', True )

    return result

  @property
  def score( self ):
    if self.ran_at is None:
      return None

    score_list = []
    for target in self.resource_map:
      for i in range( 0, len( self.resource_map[ target ] ) ):
        score_list.append( self.resource_map[ target ][ i ].get( 'score', None ) )

    return score_list

  @cinp.action( paramater_type_list=[ { 'type': '_USER_' } ] )
  def jobRan( self, user ):
    if not user.is_anonymous() and not user.has_perm( 'Processor.can_ran' ):  # remove anonymous stuff when nullunit authencates
      raise PermissionDenied()

    if self.ran_at is not None:  # been done, don't touch
      return

    if not self.built_at:
      self.built_at = datetime.now( timezone.utc )

    self.ran_at = datetime.now( timezone.utc )
    self.full_clean()
    self.save()

  @cinp.action( paramater_type_list=[ { 'type': '_USER_' } ] )
  def acknowledge( self, user ):
    if not user.has_perm( 'Processor.can_ack' ):
      raise PermissionDenied()

    if self.acknowledged_at is not None:  # been done, don't touch
      return

    if self.reported_at is None:
      raise ValidationError( 'Can not Acknoledge un-reported jobs' )

    self.acknowledged_at = datetime.now( timezone.utc )
    self.full_clean()
    self.save()

  @cinp.action( return_type='Map', paramater_type_list=[ 'String', 'Integer', 'Integer' ] )
  def getConfigStatus( self, name, index=None, count=None ):
    try:
      config_list = self.resource_map[ name ]
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

  @cinp.action( return_type='Map', paramater_type_list=[ 'String', 'Integer', 'Integer' ] )
  def getProvisioningInfo( self, name, index=None, count=None ):
    try:
      config_list = self.resource_map[ name ]
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
      values[ 'config_values' ] = config.config_values
      values[ 'timestamp' ] = values[ 'timestamp' ].strftime( '%Y-%m-%d %H:%M:%S' )
      results[ index + pos ] = values

    return results

  @cinp.list_filter( name='project', paramater_type_list=[ { 'type': 'Model', 'model': Project } ] )
  @staticmethod
  def filter_project( project ):
    return BuildJob.objects.filter( project=project )

  @cinp.check_auth()
  @staticmethod
  def checkAuth( user, verb, id_list, action=None ):
    return True

  def clean( self, *args, **kwargs ):
    super().clean( *args, **kwargs )
    errors = {}

    if errors:
      raise ValidationError( errors )

  def __str__( self ):
    return 'BuildJob "{0}" for build "{1}"'.format( self.pk, self.build.name )


def getCookie():
  return str( uuid.uuid4() )


@cinp.model( not_allowed_verb_list=[ 'CREATE', 'DELETE', 'UPDATE', 'CALL' ] )
class Instance( models.Model ):
  resource = models.ForeignKey( Resource, on_delete=models.PROTECT )
  network = models.ForeignKey( NetworkResource, on_delete=models.PROTECT )
  cookie = models.CharField( max_length=36, default=getCookie )
  foundation = models.CharField( max_length=100, blank=True, null=True )
  structure = models.CharField( max_length=100, blank=True, null=True )
  hostname = models.CharField( max_length=100 )
  # build info
  buildjob = models.ForeignKey( BuildJob, blank=True, null=True, on_delete=models.PROTECT )
  name = models.CharField( max_length=50 )
  index = models.IntegerField()
  config_values = MapField( blank=True )
  status = models.CharField( max_length=20, default='Allocated' )  # Allocated, Building, Built1, Built, Releasing, Released1, Released
  # results info
  success = models.BooleanField( default=False )
  results = models.TextField( blank=True, null=True )
  score = models.FloatField( blank=True, null=True )
  package_files = StringListField( blank=True, null=True )
  created = models.DateTimeField( editable=False, auto_now_add=True )
  updated = models.DateTimeField( editable=False, auto_now=True )

  @cinp.action( paramater_type_list=[ 'String' ] )
  def foundationBuild( self, cookie ):  # called from webhook
    if self.cookie != self.cookie:
      return

    self.state = 'Built1'
    self.full_clean()
    self.save()

  @cinp.action( paramater_type_list=[ 'String' ] )
  def structureBuild( self, cookie ):  # called from webhook
    if self.cookie != self.cookie:
      return

    self.state = 'Built'
    self.full_clean()
    self.save()

  @cinp.action( paramater_type_list=[ 'String' ] )
  def structureDestroyed( self, cookie ):  # called from webhook
    if self.cookie != self.cookie:
      return

    self.state = 'Released1'
    self.full_clean()
    self.save()

  @cinp.action( paramater_type_list=[ 'String' ] )
  def foundationDestroyed( self, cookie ):  # called from webhook
    if self.cookie != self.cookie:
      return

    self.state = 'Released'
    self.full_clean()
    self.save()

  @cinp.action( paramater_type_list=[ 'String', 'String' ] )
  def updateResourceState( self, cookie, status ):
    if self.cookie != self.cookie:
      return

    self.status = status
    self.full_clean()
    self.save()

  @cinp.action( paramater_type_list=[ 'String', 'Boolean' ] )
  def setResourceSuccess( self, cookie, success ):
    if self.cookie != self.cookie:
      return

    self.success = success
    self.full_clean()
    self.save()

  @cinp.action( paramater_type_list=[ 'String', 'String' ] )
  def setResourceResults( self, cookie, results ):
    if self.cookie != self.cookie:
      return

    self.results = results
    self.full_clean()
    self.save()

  @cinp.action( paramater_type_list=[ 'String', 'Float' ] )
  def setResourceScore( self, cookie, score ):
    if self.cookie != self.cookie:
      return

    self.score = score
    self.full_clean()
    self.save()

  @cinp.action( return_type='String', paramater_type_list=[ 'String', { 'type': 'String', 'is_array': True } ] )
  def addPackageFiles( self, cookie, package_files ):
    if self.cookie != self.cookie:
      return

    self.package_files = package_files
    self.full_clean()
    self.save()

  def release( self ):
    self.resource.release()

  def build():
    pass

  @property
  def built( self ):
    return self.state == 'Built'

  @property
  def released( self ):
    return self.state == 'Released'

  @cinp.check_auth()
  @staticmethod
  def checkAuth( user, verb, id_list, action=None ):
    return True

  def __str__( self ):
    return 'Instance "{0}" for BuildJob "{1}" Named "{2}"'.format( self.pk. self.buildjob, self.hostname )
