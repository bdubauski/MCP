import uuid
from datetime import datetime, timezone

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

from cinp.orm_django import DjangoCInP as CInP

from mcp.lib.t3kton import getContractor
from mcp.fields import MapField, StringListField

from mcp.Project.models import Build, Project, PackageVersion, Commit, TAG_NAME_LENGTH
from mcp.Resource.models import Resource, NetworkResource


cinp = CInP( 'Processor', '0.1' )


BUILDJOB_STATE_LIST = ( 'new', 'build', 'ran', 'reported', 'acknowledged', 'released' )
INSTANCE_STATE_LIST = ( 'allocated', 'building', 'built1', 'built', 'releasing', 'released1', 'released' )


# techinically we sould be grouping all the same build to geather, but sence each package has a diffrent distro name in the version we end up
# with multiple "versions" for one "version" of the file.  So hopfully the rest of MCP maintains one commit at a time, and we will group
# all versions of a package togeather in the same Promotion for now, better logic is needed eventually
@cinp.model( not_allowed_verb_list=[ 'CREATE', 'DELETE', 'UPDATE', 'CALL' ] )
class Promotion( models.Model ):
  package_versions = models.ManyToManyField( PackageVersion, through='PromotionPkgVersion', help_text='' )
  status = models.ManyToManyField( Build, through='PromotionBuild', help_text='' )
  tag = models.CharField( max_length=TAG_NAME_LENGTH )
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
    return 'Promotion for package/versions {0} tag "{1}"'.format( [ ( '{0}({1})'.format( i.package.name, i.version ) ) for i in self.package_versions.all() ], self.tag )


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
    return 'PromotionPkgVersion for package "{0}" version "{1}" for tag "{2}"'.format( self.package_version.package.name, self.package_version.version, self.promotion.tag )

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
    return 'PromotionBuild for tag "{0}" using build "{1}" at "{2}"'.format( self.promotion.tag, self.build.name, self.status )

  class Meta:
    unique_together = ( 'promotion', 'build' )


@cinp.model( not_allowed_verb_list=[ 'CREATE', 'DELETE', 'UPDATE' ] )
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
  user = models.CharField( max_length=150 )
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
    for buildresource in self.build.buildresource_set.all():
      name = buildresource.name
      quanity = buildresource.quanity
      resource = buildresource.resource.subclass
      resource.allocate( job, name, quanity, target_network )

  @staticmethod
  def inQueueBuild( build, branch, manual, priority, user, promotion=None ):
    item = QueueItem()
    item.user = user
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
  def inQueueTarget( project, branch, manual, distro, target, priority, user, commit=None ):
    try:
      build = Build.objects.get( project_id='_builtin_', name=distro )
    except Build.DoesNotExist:
      raise Exception( 'distro "{0}" not set up'.format( distro ) )

    item = QueueItem()
    item.user = user
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
    # if not user.has_perm( 'Processor.can_build' ):
    #   raise PermissionDenied()

    item = QueueItem.inQueueBuild( build, 'master', True, 100, user.username )
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


@cinp.model( not_allowed_verb_list=[ 'CREATE', 'DELETE', 'UPDATE' ], property_list=[ { 'name': 'state', 'choices': BUILDJOB_STATE_LIST }, { 'name': 'suceeded', 'type': 'Boolean' }, { 'name': 'instance_summary', 'type': 'Map' } ] )
class BuildJob( models.Model ):
  """
BuildJob
  """
  build = models.ForeignKey( Build, on_delete=models.PROTECT, editable=False )  # don't delete Builds/projects when things are in flight
  project = models.ForeignKey( Project, on_delete=models.PROTECT, editable=False )
  branch = models.CharField( max_length=50 )
  target = models.CharField( max_length=50 )
  build_name = models.CharField( max_length=50 )
  value_map = MapField( default={}, blank=True )  # for the job to store work values
  built_at = models.DateTimeField( editable=False, blank=True, null=True )
  ran_at = models.DateTimeField( editable=False, blank=True, null=True )
  reported_at = models.DateTimeField( editable=False, blank=True, null=True )
  acknowledged_at = models.DateTimeField( editable=False, blank=True, null=True )
  released_at = models.DateTimeField( editable=False, blank=True, null=True )
  manual = models.BooleanField()
  user = models.CharField( max_length=150 )
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

  # some jobs have more than one instances, in this case, if a instance hasn't
  # report a status we will assume it has success, due to the fact that many
  # of the sub instances will never report
  @property
  def suceeded( self ):
    if self.ran_at is None:
      return None

    result = True
    for instance in self.instance_set.all():
      result &= instance.success

    return result

  @property
  def instance_summary( self ):
    if self.commit is not None:
      if self.target == 'test':
        lint_map = self.commit.getResults( 'lint' )
        test_map = self.commit.getResults( 'test' )
        results_map = {}
        for name in lint_map:
          results_map[ name ] = 'lint:\n{0}\n\ntest:\n{1}'.format( lint_map[ name ] if lint_map[ name ] is not None else '', test_map[ name ] if test_map[ name ] is not None else '' )

      else:
        results_map = self.commit.getResults( self.target )

      score_map = self.commit.getScore( self.target )

    else:
      results_map = {}
      score_map = {}

    result = {}
    for instance in self.instance_set.all():
      item = {
                'id': instance.pk,
                'success': instance.success,
                'state': instance.state,
                'message': instance.message
              }

      try:
        item[ 'results' ] = results_map[ instance.name ]
      except KeyError:
        pass

      try:
        item[ 'score' ] = score_map[ instance.name ]
      except KeyError:
        pass

      try:
        result[ instance.name ][ instance.index ] = item
      except KeyError:
        result[ instance.name ] = { instance.index: item }

    return result

  def _jobRan( self ):
    if self.ran_at is not None:  # been done, don't touch
      return

    if not self.built_at:
      self.built_at = datetime.now( timezone.utc )

    self.ran_at = datetime.now( timezone.utc )
    self.full_clean()
    self.save()

  @cinp.action( paramater_type_list=[ { 'type': '_USER_' } ] )
  def jobRan( self, user ):
    # if not user.has_perm( 'Processor.can_ran' ):
    #   raise PermissionDenied()

    self._jobRan()

  @cinp.action( paramater_type_list=[ { 'type': '_USER_' } ] )
  def acknowledge( self, user ):
    # if not user.has_perm( 'Processor.can_ack' ):
    #   raise PermissionDenied()

    if self.acknowledged_at is not None:  # been done, don't touch
      return

    if self.reported_at is None:
      raise ValidationError( 'Can not Acknoledge un-reported jobs' )

    self.acknowledged_at = datetime.now( timezone.utc )
    self.full_clean()
    self.save()

  @cinp.action( return_type='Map', paramater_type_list=[ 'String' ] )
  def getInstanceState( self, name=None ):
    result = {}
    if name is not None:
      for instance in self.instance_set.all():
        if instance.name != name:
          continue

        result[ instance.index ] = instance.state

    else:
      for instance in self.instance_set.all():
        try:
          result[ instance.name ][ instance.index ] = instance.state
        except KeyError:
          result[ instance.name ] = { instance.index: instance.state }

    return result

  @cinp.action( return_type='Map', paramater_type_list=[ 'String' ] )
  def getInstanceDetail( self, name=None ):
    result = {}
    if name is not None:
      for instance in self.instance_set.all():
        if instance.name != name:
          continue

        result[ instance.index ] = instance.getDetail()

    else:
      for instance in self.instance_set.all():
        try:
          result[ instance.name ][ instance.index ] = instance.getDetail()
        except KeyError:
          result[ instance.name ] = { instance.index: instance.getDetail() }

    return result

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


@cinp.model( not_allowed_verb_list=[ 'CREATE', 'DELETE', 'UPDATE' ], property_list=[ 'config_values' ] )
class Instance( models.Model ):
  resource = models.ForeignKey( Resource, on_delete=models.PROTECT )
  network = models.ForeignKey( NetworkResource, on_delete=models.PROTECT )
  cookie = models.CharField( max_length=36, default=getCookie )
  hostname = models.CharField( max_length=100 )
  # build info
  buildjob = models.ForeignKey( BuildJob, blank=True, null=True, on_delete=models.PROTECT )
  name = models.CharField( max_length=50, blank=True, null=True  )
  index = models.IntegerField( blank=True, null=True )
  state = models.CharField( max_length=9, default='allocated', choices=[ ( i, i ) for i in INSTANCE_STATE_LIST ] )
  message = models.CharField( max_length=200, default='', blank=True )
  # results info
  success = models.BooleanField( default=False )
  package_files = StringListField( blank=True, null=True )
  created = models.DateTimeField( editable=False, auto_now_add=True )
  updated = models.DateTimeField( editable=False, auto_now=True )
  # contractor specific
  foundation_id = models.CharField( max_length=100, blank=True, null=True )
  structure_id = models.CharField( max_length=100, blank=True, null=True )

  @property
  def config_values( self ):
    result = {
               'mcp_host': settings.MCP_HOST,
               'mcp_proxy': ( settings.MCP_PROXY if settings.MCP_PROXY else '' ),
               'packrat_host': 'http://packrat',
               'packrat_builder_name': 'nullunit',
               'packrat_builder_password': 'nullunit',
               'confluence_host': 'http://confluence',
               'confluence_username': 'mcp',
               'confluence_password': 'mcp'
             }

    if self.buildjob is not None:
      result.update( {
                       'mcp_job_id': self.buildjob.pk,
                       'mcp_instance_id': self.pk,
                       'mcp_build_name': self.buildjob.build_name,
                       'mcp_instance_cookie': self.cookie,
                       'mcp_resource_name': self.name,
                       'mcp_resource_index': self.index,
                       'mcp_store_packages': self.buildjob.branch == 'master',
                       'mcp_git_url': self.buildjob.project.internal_git_url,
                       'mcp_git_branch': self.buildjob.branch,
                       'mcp_make_target': self.buildjob.target
                      } )

    return result

  @cinp.action( paramater_type_list=[ 'String' ] )   # TODO: do we need all this complicated callback stuff now that we can create both jobs from the start?, and for that metter the end?
  def foundationBuild( self, cookie ):  # called from webhook
    if self.cookie != cookie:
      return

    self.state = 'built1'
    self.full_clean()
    self.save()

    contractor = getContractor()
    contractor.createStructure( self.structure_id )

  @cinp.action( paramater_type_list=[ 'String' ] )
  def structureBuild( self, cookie ):  # called from webhook
    if self.cookie != cookie:
      return

    self.state = 'built'
    self.full_clean()
    self.save()

  @cinp.action( paramater_type_list=[ 'String' ] )
  def foundationDestroyed( self, cookie ):  # called from webhook
    if self.cookie != cookie:
      return

    contractor = getContractor()
    contractor.deleteFoundation( self.foundation_id )

    self.state = 'released'
    self.foundation_id = None
    self.full_clean()
    self.save()

  @cinp.action( paramater_type_list=[ 'String' ] )
  def structureDestroyed( self, cookie ):  # called from webhook
    if self.cookie != cookie:
      return

    contractor = getContractor()
    contractor.deleteStructure( self.structure_id )
    contractor.destroyFoundation( self.foundation_id )

    self.state = 'released1'
    self.structure_id = None
    self.full_clean()
    self.save()

  @cinp.action( paramater_type_list=[ 'String', 'String' ] )
  def setMessage( self, cookie, message ):
    if self.cookie != cookie:
      return

    self.message = message[ -200: ]
    self.full_clean()
    self.save()

  @cinp.action( paramater_type_list=[ 'String' ] )
  def jobRan( self, cookie ):
    if self.cookie != cookie:
      return

    self.buildjob._jobRan()

  @cinp.action( paramater_type_list=[ 'String', 'Boolean' ] )
  def setSuccess( self, cookie, success ):
    if self.cookie != cookie:
      return

    self.success = success
    self.full_clean()
    self.save()

  @cinp.action( paramater_type_list=[ 'String', 'String', 'String' ] )
  def setResults( self, cookie, target, results ):
    if self.cookie != cookie:
      return

    if target != self.buildjob.target and not ( self.buildjob.target == 'test' and target in ( 'test', 'lint' ) ):
      return

    self.buildjob.commit.setResults( target, self.name, results )

  @cinp.action( paramater_type_list=[ 'String', 'String', 'Float' ] )
  def setScore( self, cookie, target, score ):
    if self.cookie != cookie:
      return

    if self.buildjob.target != 'test' or target not in ( 'test', 'lint' ):
      return

    self.buildjob.commit.setScore( target, self.name, score )

  @cinp.action( return_type='String', paramater_type_list=[ 'String', { 'type': 'String', 'is_array': True } ] )
  def addPackageFiles( self, cookie, package_files ):
    if self.cookie != cookie:
      return

    self.package_files = package_files
    self.full_clean()
    self.save()

  @cinp.action( return_type='Map', paramater_type_list=[ 'String' ]  )
  def getValueMap( self, cookie ):
    if self.cookie != cookie:
      return

    return self.buildjob.value_map

  @cinp.action( paramater_type_list=[ 'String', 'Map' ] )
  def updateValueMap( self, cookie, value_map ):
    if self.cookie != cookie:
      return

    self.buildjob.value_map.update( value_map )
    self.buildjob.full_clean()
    self.buildjob.save()

  @cinp.action( return_type='Map' )
  def getDetail( self ):  # Only called by ui.js, when nuillunitInterface get detail is working again, unify with this one
    result = {
               'foundation_id': self.foundation_id,
               'structure_id': self.structure_id,
               'hostname': self.hostname
              }
    return result

  def build( self ):
    if self.state in ( 'building', 'built1', 'built' ):
      return

    if self.state in ( 'releasing', 'released1', 'released' ):
      raise Exception( 'Can not build while released/releasing' )

    self.resource.subclass.build( self )

    self.state = 'building'
    self.full_clean()
    self.save()

  def release( self ):
    if self.state in ( 'releasing', 'released1', 'released' ):
      return

    if self.state not in ( 'built', ):
      raise Exception( 'Can not release when not built' )

    self.resource.subclass.release( self )

    self.state = 'releasing'
    self.full_clean()
    self.save()

  @cinp.check_auth()
  @staticmethod
  def checkAuth( user, verb, id_list, action=None ):
    return True

  def __str__( self ):
    return 'Instance "{0}" for BuildJob "{1}" Named "{2}"'.format( self.pk, self.buildjob, self.hostname )
