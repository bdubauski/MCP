import uuid
from datetime import datetime, timezone

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

from cinp.orm_django import DjangoCInP as CInP

from mcp.fields import MapField, package_filename_regex, packagefile_regex, TAG_NAME_LENGTH, BLUEPRINT_NAME_LENGTH

from mcp.Project.models import Build, Project, Commit
from mcp.Resource.models import ResourceInstance, Network


cinp = CInP( 'Processor', '0.1' )

BUILDJOB_STATE_LIST = ( 'new', 'build', 'ran', 'reported', 'acknowledged', 'released' )
INSTANCE_STATE_LIST = ( 'new', 'allocated', 'building', 'built', 'ran', 'releasing', 'released' )


def base_config_values():
  return {
           '>package_list': [ 'nullunit' ],
           'packrat_host': 'http://packrat',
           'packrat_proxy': '',
           'confluence_host': 'http://confluence',
           'confluence_proxy': '',
           'nullunit_packrat_username': 'nullunit',
           'nullunit_packrat_password': 'nullunit',
           'nullunit_confluence_username': 'nullunit',
           'nullunit_confluence_password': 'nullunit',
           'mcp_host': settings.MCP_HOST,
           'mcp_proxy': ( settings.MCP_PROXY if settings.MCP_PROXY else '' )
         }


@cinp.model( not_allowed_verb_list=[ 'CREATE', 'DELETE', 'UPDATE', 'CALL' ] )
class Promotion( models.Model ):
  status = models.ManyToManyField( Build, through='PromotionBuild', help_text='' )
  result_map = MapField( blank=True )
  commit = models.ForeignKey( Commit, on_delete=models.PROTECT )
  tag = models.CharField( max_length=TAG_NAME_LENGTH )
  done_at = models.DateTimeField( blank=True, null=True )
  created = models.DateTimeField( editable=False, auto_now_add=True )
  updated = models.DateTimeField( editable=False, auto_now=True )

  def signalComplete( self, build, success ):
    promotion_build = self.promotionbuild_set.get( build=build )
    promotion_build.status = 'done'
    promotion_build.success = success
    promotion_build.full_clean()
    promotion_build.save()

  def setResults( self, name, results ):
    self.result_map[ name ] = results
    self.full_clean()
    self.save()

  def getResults( self ):
    return self.result_map

  @cinp.list_filter( name='in_process', paramater_type_list=[] )
  @staticmethod
  def filter_in_process():
    return Promotion.objects.filter( done_at__isnull=True )

  @cinp.check_auth()
  @staticmethod
  def checkAuth( user, verb, id_list, action=None ):
    return cinp.basic_auth_check( user, verb, Promotion )

  class Meta:
    default_permissions = ()

  def __str__( self ):
    return 'Promotion for package commit "{0}" tag "{1}"'.format( self.commit, self.tag )


@cinp.model( not_allowed_verb_list=[ 'CREATE', 'DELETE', 'UPDATE', 'CALL' ] )
class PromotionBuild( models.Model ):
  promotion = models.ForeignKey( Promotion, on_delete=models.CASCADE )
  build = models.ForeignKey( Build, on_delete=models.CASCADE )
  status = models.CharField( max_length=50 )
  success = models.NullBooleanField( null=True )

  @cinp.check_auth()
  @staticmethod
  def checkAuth( user, verb, id_list, action=None ):
    return cinp.basic_auth_check( user, verb, PromotionBuild )

  class Meta:
    unique_together = ( 'promotion', 'build' )
    default_permissions = ()

  def __str__( self ):
    return 'PromotionBuild for tag "{0}" using build "{1}" at "{2}"'.format( self.promotion.tag, self.build.name, self.status )


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

  def allocateResources( self ):
    missing_list = []
    buildresource_list = []
    network_map = {}
    other_ip_count = 0

    # first allocate the network(s)
    for name, item in self.build.network_map.items():
      if item[ 'dedicated' ]:
        try:
          network_map[ name ] = Network.objects.filter( monolithic=True, size__gte=item[ 'min_addresses' ], buildjob__isnull=True )[ 0 ].name
        except IndexError:
          missing_list.append( 'Network for "{0}" Not Available'.format( name ) )

      else:
        for network in Network.objects.filter( monolithic=False, size__gte=item[ 'min_addresses' ] ):
          if network.available( item[ 'min_addresses' ] ):
             network_map[ name ] = network.name
             break

        try:
          network[ name ]
        except KeyError:
          missing_list.append( 'Network for "{0}" Not Available'.format( name ) )

    # second allocate the resource(s)
    for buildresource in self.build.buildresource_set.all():
      quantity = buildresource.quantity
      resource = buildresource.resource.subclass
      if not resource.available( quantity, buildresource.interface_map ):
        missing_list.append( 'Resource "{0}" Not Available'.format( resource.name ) )

      buildresource_list.append( buildresource )

      for item in buildresource.interface_map.values():
        if 'network' in item:
          try:
            network_map[ item[ 'network' ] ]
          except KeyError:
            missing_list.append( 'Network "{0}" Not Defined'.format( item[ 'network' ] ) )

        else:
          other_ip_count += quantity

    # lastly make sure we have the IPs
    if other_ip_count:
      for network in Network.objects.filter( monolithic=False, size__gte=other_ip_count ).exclude( pk__in=network_map.items() ):
        if network.available( other_ip_count ):
           network_map[ '_OTHER_' ] = network.name
           break

      try:
        network_map[ '_OTHER_' ]
      except KeyError:
        missing_list.append( 'Other Network Not Available' )

    if missing_list:
      return ( list( set( missing_list ) ), None, None )

    return ( None, buildresource_list, network_map )

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
  def inQueueTarget( project, branch, manual, blueprint, target, priority, user, commit=None ):
    try:
      builtin_project = Project( pk='_builtin_' )
    except Project.DoesNotExist:
      raise Exception( 'project "_builtin_" missing' )

    try:
      build = Build.objects.get( project=builtin_project, buildresource__blueprint=blueprint )
    except Build.DoesNotExist:
      raise Exception( 'build for _builtin_ project and blueprint "{0}" not found'.format( blueprint ) )

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

  @cinp.action( return_type='Integer', paramater_type_list=[ { 'type': '_USER_' }, { 'type': 'Model', 'model': Build }, 'String', 'Integer' ] )
  @staticmethod
  def queue( user, build, branch=None, priority=100 ):
    if branch is None:
      branch = build.project.release_branch

    item = QueueItem.inQueueBuild( build, branch, True, priority, user.username )
    return item.pk

  @cinp.list_filter( name='project', paramater_type_list=[ { 'type': 'Model', 'model': Project } ] )
  @staticmethod
  def filter_project( project ):
    return QueueItem.objects.filter( project=project )

  @cinp.check_auth()
  @staticmethod
  def checkAuth( user, verb, id_list, action=None ):
    if not cinp.basic_auth_check( user, verb, QueueItem ):
      return False

    if verb == 'CALL':
      if action == 'queue' and user.has_perm( 'Processor.can_build' ):
        return True

      return False

    else:
      return True

  class Meta:
    default_permissions = ()

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
  value_map = MapField( blank=True )  # for the job to store work values
  network_list = models.ManyToManyField( Network )
  resources = models.ManyToManyField( ResourceInstance, through='BuildJobResourceInstance' )
  built_at = models.DateTimeField( editable=False, blank=True, null=True )
  ran_at = models.DateTimeField( editable=False, blank=True, null=True )
  reported_at = models.DateTimeField( editable=False, blank=True, null=True )
  acknowledged_at = models.DateTimeField( editable=False, blank=True, null=True )
  released_at = models.DateTimeField( editable=False, blank=True, null=True )
  manual = models.BooleanField()
  user = models.CharField( max_length=150 )
  commit = models.ForeignKey( Commit, null=True, blank=True, on_delete=models.SET_NULL )
  promotion = models.ForeignKey( Promotion, null=True, blank=True, on_delete=models.SET_NULL )
  package_file_map = MapField( blank=True )
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
    for instance in self.buildjobresourceinstance_set.all():
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

    if self.promotion is not None:
      results_map = self.promotion.getResults()
      score_map = {}

    else:
      results_map = {}
      score_map = {}

    result = {}
    for instance in self.buildjobresourceinstance_set.all():
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

  @cinp.action( paramater_type_list=[ { 'type': '_USER_' } ] )
  def jobRan( self, user ):
    if self.ran_at is not None:  # been done, don't touch
      return

    if not self.built_at:
      self.built_at = datetime.now( timezone.utc )

    self.ran_at = datetime.now( timezone.utc )
    self.full_clean()
    self.save()

  @cinp.action( paramater_type_list=[ { 'type': '_USER_' } ] )
  def acknowledge( self, user ):
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
      for instance in self.buildjobresourceinstance_set.all():
        if instance.name != name:
          continue

        result[ instance.index ] = instance.state

    else:
      for instance in self.buildjobresourceinstance_set.all():
        try:
          result[ instance.name ][ instance.index ] = instance.state
        except KeyError:
          result[ instance.name ] = { instance.index: instance.state }

    return result

  @cinp.action( return_type='Map', paramater_type_list=[ 'String' ] )
  def getInstanceDetail( self, name=None ):
    result = {}
    if name is not None:
      for instance in self.buildjobresourceinstance_set.all():
        if instance.name != name:
          continue

        result[ instance.index ] = instance.getDetail()

    else:
      for instance in self.buildjobresourceinstance_set.all():
        try:
          result[ instance.name ][ instance.index ] = instance.getDetail()
        except KeyError:
          result[ instance.name ] = { instance.index: instance.getDetail() }

    return result

  def buildResources( self ):
    for instance in self.buildjobresourceinstance_set.all():
        instance.build()

  def releaseResources( self ):
    for instance in self.buildjobresourceinstance_set.all():
        instance.release()

  @property
  def instances_built( self ):
    for instance in self.buildjobresourceinstance_set.all():
      if instance.state not in ( 'built', 'ran', 'releasing', 'released' ):
        return False

    return True

  @property
  def instances_ran( self ):
    for instance in self.buildjobresourceinstance_set.all():
      if instance.state not in ( 'ran', 'releasing', 'released' ):
        return False

    return True

  @property
  def instances_released( self ):
    for instance in self.buildjobresourceinstance_set.all():
      if instance.state != 'released':
        return False

    return True

  @cinp.list_filter( name='project', paramater_type_list=[ { 'type': 'Model', 'model': Project } ] )
  @staticmethod
  def filter_project( project ):
    return BuildJob.objects.filter( project=project )

  @cinp.check_auth()
  @staticmethod
  def checkAuth( user, verb, id_list, action=None ):
    if not cinp.basic_auth_check( user, verb, BuildJob ):
      return False

    if verb == 'CALL':
      if action in ( 'getInstanceState', 'getInstanceDetail' ):
        return True

      if action == 'jobRan' and user.has_perm( 'Processor.can_ran' ):
        return True

      if action == 'acknowledge' and user.has_perm( 'Processor.can_ack' ):
        return True

      return False

    else:
      return True

  def clean( self, *args, **kwargs ):
    super().clean( *args, **kwargs )
    errors = {}

    for key, value in self.package_file_map.items():
      if not package_filename_regex.match( key ):
        errors[ 'package_file_map' ] = 'file name "{0}" invalid'.format( key )
        break

      if not isinstance( value, str ) and not packagefile_regex.match( value ):
        errors[ 'package_file_map' ] = 'file uri invalid for "{0}"'.format( key )
        break

    if errors:
      raise ValidationError( errors )

  def delete( self, *args, **kwargs ):
    for instance in self.buildjobresourceinstance_set.all():
      instance.delete()

    super().delete( *args, **kwargs )

  class Meta:
    default_permissions = ()
    permissions = (
                    ( 'can_build', 'Can queue builds' ),
                    ( 'can_ran', 'Can Flag a Build Resource as ran' ),
                    ( 'can_ack', 'Can Acknoledge a failed Build Resource' )
    )

  def __str__( self ):
    return 'BuildJob "{0}" for build "{1}"'.format( self.pk, self.build.name )


def getCookie():
  return str( uuid.uuid4() )


@cinp.model( not_allowed_verb_list=[ 'CREATE', 'DELETE', 'UPDATE' ], property_list=[ 'config_values', 'hostname' ] )
class BuildJobResourceInstance( models.Model ):
  buildjob = models.ForeignKey( BuildJob, blank=True, null=True, on_delete=models.PROTECT )  # protected so we don't leave stranded resources
  resource_instance = models.OneToOneField( ResourceInstance, blank=True, null=True, on_delete=models.SET_NULL )
  blueprint = models.CharField( max_length=BLUEPRINT_NAME_LENGTH )
  _config_values = MapField( blank=True )
  autorun = models.BooleanField( default=False )
  cookie = models.CharField( max_length=36, default=getCookie )
  # build info
  name = models.CharField( max_length=50, blank=True, null=True  )
  index = models.IntegerField( blank=True, null=True )
  state = models.CharField( max_length=9, default='new', choices=[ ( i, i ) for i in INSTANCE_STATE_LIST ] )
  message = models.CharField( max_length=200, default='', blank=True )
  # results info
  success = models.BooleanField( default=False )
  created = models.DateTimeField( editable=False, auto_now_add=True )
  updated = models.DateTimeField( editable=False, auto_now=True )

  @property
  def hostname( self ):  # TODO: make sure does not exceed contractor's locator length, and is locator/hostname safe
    if self.buildjob is not None:
      if self.buildjob.manual:
        return 'mcp-manual--{0}-{1}-{2}'.format( self.buildjob_id, self.name, self.index )
      else:
        return 'mcp-auto--{0}-{1}-{2}'.format( self.buildjob_id, self.name, self.index )

    else:
      return 'mcp-prealloc--{0}'.format( self.pk )

  @property
  def config_values( self ):
    result = self._config_values

    result.update( base_config_values() )

    if self.buildjob is not None:
      result.update( {
                       'mcp_job_id': self.buildjob.pk,
                       'mcp_instance_id': self.pk,
                       'mcp_build_name': self.buildjob.build_name,
                       'mcp_project_name': self.buildjob.project.name,
                       'mcp_instance_cookie': self.cookie,
                       'mcp_resource_name': self.name,
                       'mcp_resource_index': self.index,
                       'mcp_store_packages': self.buildjob.branch == self.buildjob.project.release_branch,
                       'mcp_git_url': self.buildjob.project.internal_git_url,
                       'mcp_git_branch': self.buildjob.branch,
                       'mcp_make_target': self.buildjob.target
                      } )

      if self.buildjob.commit is not None:
        result.update( {
                         'mcp_commit_version': self.buildjob.commit.version
                        } )

      if self.buildjob.promotion is not None:
        result.update( {
                         'mcp_promotion_tag': self.buildjob.promotion.tag
                        } )

    return result

  @config_values.setter
  def config_values( self, value):
    self._config_values = value

  @cinp.action( paramater_type_list=[ 'String' ] )
  def signal_built( self, cookie ):  # called from webhook
    if self.cookie != cookie:
      return

    if self.state not in ( 'new', 'allocated', 'building' ):  # allready moved on, don't touch
      return

    if self.autorun:
      self.state = 'ran'
      self.success = True

    else:
      self.state = 'built'

    self.full_clean()
    self.save()

  @cinp.action( paramater_type_list=[ 'String' ] )
  def signal_destroyed( self, cookie ):  # called from webhook
    if self.cookie != cookie:
      return

    self.resource_instance.cleanup()

    self.resource_instance = None  # techinically this is done for us
    self.state = 'released'
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

    if self.state not in ( 'new', 'allocated', 'building', 'built' ):  # don't go back to a previous state
      return

    self.state = 'ran'
    self.full_clean()
    self.save()

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

    if self.buildjob.commit:
      self.buildjob.commit.setResults( target, self.name, results )
    elif self.buildjob.promotion:
      self.buildjob.promotion.setResults( self.name, results )

  @cinp.action( paramater_type_list=[ 'String', 'String', 'Float' ] )
  def setScore( self, cookie, target, score ):
    if self.cookie != cookie:
      return

    if self.buildjob.target != 'test' or target not in ( 'test', 'lint' ):
      return

    if self.buildjob.commit:
      self.buildjob.commit.setScore( target, self.name, score )

  @cinp.action( return_type='String', paramater_type_list=[ 'String', { 'type': 'Map' } ] )
  def addPackageFiles( self, cookie, package_file_map ):
    if self.cookie != cookie:
      return

    self.buildjob.package_file_map.update( package_file_map )
    self.buildjob.full_clean()
    self.buildjob.save()

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
               'structure_id': self.resource_instance.contractor_structure_id,
               'hostname': self.hostname
              }

    return result

  def allocate( self ):
    if self.state != 'new':
      raise Exception( 'Allready allocated' )

    self.resource_instance.allocate( self.blueprint, self.config_values, self.hostname )

    self.state = 'allocated'
    self.full_clean()
    self.save()

  def updateConfig( self ):
    if self.state in ( 'releasing', 'released' ):
      return

    self.resource_instance.updateConfig( self.config_values, self.hostname )

  def build( self ):
    if self.state in ( 'building', 'built' ):
      return

    if self.state != 'allocated':
      raise Exception( 'Can only build when allocated' )

    self.resource_instance.build()

    self.state = 'building'
    self.full_clean()
    self.save()

  def release( self ):
    if self.state in ( 'releasing', 'released' ):
      return

    if self.state == 'new':
      self.state = 'released'
      self.full_clean()
      self.save()
      return

    elif self.state == 'allocated':
      if self.resource_instance is not None:
        self.resource_instance.cleanup()

      self.state = 'released'
      self.full_clean()
      self.save()
      return

    if self.state not in ( 'built', 'ran' ):
      raise Exception( 'Can not release when not built' )

    if self.resource_instance is None:
      self.state = 'released'
      self.full_clean()
      self.save()
      return

    self.resource_instance.release()

    self.state = 'releasing'
    self.full_clean()
    self.save()

  @cinp.check_auth()
  @staticmethod
  def checkAuth( user, verb, id_list, action=None ):
    return cinp.basic_auth_check( user, verb, BuildJobResourceInstance )

  class Meta:
    default_permissions = ()

  def __str__( self ):
    return 'BuildJobResourceInstance "{0}" for BuildJob "{1}" Named "{2}"'.format( self.pk, self.buildjob, self.hostname )
