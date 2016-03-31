import re

from django.utils import simplejson
from django.db import models
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.conf import settings

from mcp.lib.GitHub import GitHub
from mcp.Resource.models import Resource

# from packrat Repos/models.py
RELEASE_TYPE_LENGTH = 5
RELEASE_TYPE_CHOICES = ( ( 'ci', 'CI' ), ( 'dev', 'Development' ), ( 'stage', 'Staging' ), ( 'prod', 'Production' ), ( 'depr', 'Deprocated' ) )

class Project( models.Model ):
  """
This is a Generic Project
  """
  name = models.CharField( max_length=50, primary_key=True )
  local_path = models.CharField( max_length=50, null=True, blank=True, editable=False )
  last_checked = models.DateTimeField()
  created = models.DateTimeField( editable=False, auto_now_add=True )
  updated = models.DateTimeField( editable=False, auto_now=True )

  @property
  def type( self ):
    try:
      self.gitproject
      return 'GitProject'
    except ObjectDoesNotExist:
      pass

    try:
      self.githubproject
      return 'GitHubProject'
    except ObjectDoesNotExist:
      pass

    return 'Project'

  @property
  def org( self ):
    try:
      return self.githubproject._org
    except ObjectDoesNotExist:
      return None

  @property
  def repo( self ):
    try:
      return self.githubproject._repo
    except ObjectDoesNotExist:
      return None

  @property
  def busy( self ): # ie. can it be updated, and scaned for new things to do
    not_busy = True
    for build in self.build_set.all():
      for item in build.queueitem_set.all():
        not_busy &= item.manual

      for job in build.buildjob_set.all():
        not_busy &= job.manual

    return not not_busy

  @property
  def internal_git_url( self ):
    return '%s%s' % ( settings.GIT_HOST, self.local_path )

  @property
  def upstream_git_url( self ):
    try:  # for now we only support git based projects
      return '%s/%s/%s.git' % ( settings.GITHUB_HOST, self.githubproject.org, self.githubproject.repo )
    except ObjectDoesNotExist:
      pass

    try:
      return self.gitproject.git_url
    except ObjectDoesNotExist:
      pass

    return None

  @property
  def clone_git_url( self ):
    try:  # for now we only support git based projects
      return ( '%s%s/%s.git' % ( settings.GITHUB_HOST, self.githubproject.org, self.githubproject.repo ) ).replace( '://', '://%s:%s@' % ( settings.GITHUB_USER, settings.GITHUB_PASS ) )
    except ObjectDoesNotExist:
      pass

    try:
      return self.gitproject.git_url
    except ObjectDoesNotExist:
      pass

    return None

  @property
  def status( self ):
    try:
      commit = self.commit_set.filter( branch='master', done_at__isnull=False ).order_by( '-created' )[0]
    except IndexError:
      return { 'passed': None, 'built': None, 'at': None }

    return { 'passed': commit.passed, 'built': commit.built, 'at': commit.created.isoformat() }

  def save( self, *args, **kwargs ):
    if not re.match( '^[a-z0-9][a-z0-9\-]*[a-z0-9]$', self.name ):
      raise ValidationError( 'Invalid name' )

    if not self.local_path:
      self.local_path = None

    super( Project, self ).save( *args, **kwargs )

  def __unicode__( self ):
    return 'Project "%s"' % self.name

  class API:
    not_allowed_methods = ( 'CREATE', 'DELETE', 'UPDATE', 'CALL' )
    properties = ( 'type', 'org', 'repo', 'busy', 'upstream_git_url', 'internal_git_url', 'status' )
    hide_fields = ( 'local_path', )


class GitProject( Project ):
  """
This is a Git Project
  """
  git_url = models.CharField( max_length=200 )

  def __unicode__( self ):
    return 'Git Project "%s"' % self.name

  class API:
    not_allowed_methods = ( 'CREATE', 'DELETE', 'UPDATE', 'CALL' )


class GitHubProject( Project ):
  """
This is a GitHub Project
  """
  _org = models.CharField( max_length=50 )
  _repo = models.CharField( max_length=50 )

  @property
  def org( self ):
    try:
      return self.githubproject._org
    except ObjectDoesNotExist:
      return None

  @property
  def repo( self ):
    try:
      return self.githubproject._repo
    except ObjectDoesNotExist:
      return None

  @property
  def github( self ):
    try:
      if self._github:
        return self._github
    except AttributeError:
      pass

    self._github = GitHub( settings.GITHUB_API_HOST, settings.GITHUB_PROXY, settings.GITHUB_USER, settings.GITHUB_PASS, self.org, self.repo )
    return self._github

  def __unicode__( self ):
    return 'GitHub Project "%s"(%s/%s)' % ( self.name, self._org, self._repo )

  class API:
    not_allowed_methods = ( 'CREATE', 'DELETE', 'UPDATE', 'CALL' )


class Package( models.Model ):
  """
This is a Package
  """
  name = models.CharField( max_length=100, primary_key=True )
  created = models.DateTimeField( editable=False, auto_now_add=True )
  updated = models.DateTimeField( editable=False, auto_now=True )

  def save( self, *args, **kwargs ):
    if not re.match( '^[a-z0-9][a-z0-9\-]*[a-z0-9]$', self.name ):
      raise ValidationError( 'Invalid name' )

    super( Package, self ).save( *args, **kwargs )

  def __unicode__( self ):
    return 'Package "%s"' % self.name

  class API:
    not_allowed_methods = ( 'CREATE', 'DELETE', 'UPDATE', 'CALL' )


class PackageVersion( models.Model ):
  """
This is a Version of a Package
  """
  package = models.ForeignKey( Package )
  version = models.CharField( max_length=50 )
  state = models.CharField( max_length=RELEASE_TYPE_LENGTH, choices=RELEASE_TYPE_CHOICES )
  created = models.DateTimeField( editable=False, auto_now_add=True )
  updated = models.DateTimeField( editable=False, auto_now=True )

  def __unicode__( self ):
    return 'PackageVersion "%s" verison "%s"' % ( self.package.name, self.version )

  class Meta:
      unique_together = ( 'package', 'version' )

  class API:
    not_allowed_methods = ( 'CREATE', 'DELETE', 'UPDATE', 'CALL' )


class Commit( models.Model ):
  """
A Single Commit of a Project
  """
  STATE_LIST = ( 'new', 'linted', 'tested', 'built', 'done' )
  project = models.ForeignKey( Project )
  owner_override = models.CharField( max_length=50, blank=True, null=True )
  branch = models.CharField( max_length=50 )
  commit = models.CharField( max_length=45 )
  lint_results = models.TextField( default='{}' )
  test_results = models.TextField( default='{}' )
  build_results = models.TextField( default='{}')
  lint_at = models.DateTimeField( editable=False, blank=True, null=True )
  test_at = models.DateTimeField( editable=False, blank=True, null=True )
  build_at = models.DateTimeField( editable=False, blank=True, null=True )
  done_at = models.DateTimeField( editable=False, blank=True, null=True )
  passed = models.NullBooleanField( editable=False, blank=True, null=True )
  built = models.NullBooleanField( editable=False, blank=True, null=True )
  created = models.DateTimeField( editable=False, auto_now_add=True )
  updated = models.DateTimeField( editable=False, auto_now=True )

  @property
  def state( self ):
    if self.done_at and self.build_at and self.test_at and self.lint_at:
      return 'done'

    if self.build_at and self.test_at and self.lint_at:
      return 'built'

    if self.test_at and self.lint_at:
      return 'tested'

    if self.lint_at:
      return 'linted'

    return 'new'

  def save( self, *args, **kwargs ):
    try:
      simplejson.loads( self.lint_results )
    except ValueError:
      raise ValidationError( 'lint_results must be valid JSON' )

    try:
      simplejson.loads( self.test_results )
    except ValueError:
      raise ValidationError( 'test_results must be valid JSON' )

    try:
      simplejson.loads( self.build_results )
    except ValueError:
      raise ValidationError( 'build_results must be valid JSON' )

    super( Commit, self ).save( *args, **kwargs )

  def signalComplete( self, target, build_name, resources ):
    if target not in ( 'lint', 'test', 'rpm', 'dpkg', 'respkg', 'resource' ):
      return

    sucess = resources[ 'target' ][0].get( 'success', False )
    results = resources[ 'target' ][0].get( 'results', None )

    if target == 'lint':
      status = simplejson.loads( self.lint_results )
      distro = build_name
      status[ distro ][ 'status' ] = 'done'
      status[ distro ][ 'success' ] = sucess
      status[ distro ][ 'results' ] = results
      self.lint_results = simplejson.dumps( status )

    elif target == 'test':
      status = simplejson.loads( self.test_results )
      distro = build_name
      status[ distro ][ 'status' ] = 'done'
      status[ distro ][ 'success' ] = sucess
      status[ distro ][ 'results' ] = results
      self.test_results = simplejson.dumps( status )

    else:
      status = simplejson.loads( self.build_results )
      distro = build_name
      status[ target ][ distro ][ 'status' ] = 'done'
      status[ target ][ distro ][ 'success' ] = sucess
      status[ target ][ distro ][ 'results' ] = results
      self.build_results = simplejson.dumps( status )

    self.save()

  def postInProcess( self ):
    if self.project.type != 'GitHubProject':
      return

    gh = self.project.githubproject.github
    if self.owner_override:
      gh.setOwner( self.owner_override )
    gh.postCommitStatus( self.commit, 'pending' )
    gh.setOwner()

  def postResults( self ):
    if self.project.type != 'GitHubProject':
      return

    gh = self.project.githubproject.github
    if self.owner_override:
      gh.setOwner( self.owner_override )

    comment = ''
    summary = ''

    if self.lint_results:
      lint = simplejson.loads( self.lint_results )
    else:
      lint = None

    if self.test_results:
      test = simplejson.loads( self.test_results )
    else:
      test = None

    if self.build_results:
      build = simplejson.loads( self.build_results )
    else:
      build = None

    if lint:
      comment += 'Lint Results:\n\n'
      for distro in lint:
        if lint[ distro ].get( 'results', None ) is not None:
          comment += '**%s**\n' % distro
          comment += '  Success: **%s**\n' % lint[ distro ].get( 'success', False )
          comment += '>' + lint[ distro ][ 'results' ].replace( '\n', '\n>' )

    if test:
      comment += 'Test Results:\n\n'
      for distro in test:
        if test[ distro ].get( 'results', None ) is not None:
          comment += '**%s**\n' % distro
          comment += '  Success: **%s**\n' % test[ distro ].get( 'success', False )
          comment += '>' + test[ distro ][ 'results' ].replace( '\n', '\n>' )

    if build:
      comment += 'Build Results:\n\n'
      for target in build:
        for distro in build[ target ]:
          if build[ target ][ distro ].get( 'results', None ) is not None:
            comment += '**%s** - **%s**\n' % ( target, distro )
            comment += '  Success: **%s**\n' % build[ target ][ distro ].get( 'success', False )
            comment += '>' + build[ target ][ distro ][ 'results' ].replace( '\n', '\n>' )

    if self.passed is not None:
      if self.passed:
        summary += 'Passed: True\n'
        gh.postCommitStatus( self.commit, 'success', description='Test/Lint Passed' )
      else:
        summary += 'Passed: False\n'
        gh.postCommitStatus( self.commit, 'failure', description='Test/Lint Failure' )

    if self.built is not None:
      if self.built:
        summary += 'Built: True\n'
      else:
        summary += 'Built: False\n'
        gh.postCommitStatus( self.commit, 'error', description='Package Build Error' )

    if not comment:
      comment = '**Nothing To Do**'

    if not summary:
      summary = '**Nothing To Do**'

    gh.postCommitComment( self.commit, comment )

    gh.setOwner()

    if self.branch.startswith( '_PR' ):
      number = int( self.branch[3:] )
      gh.postPRComment( number, summary )

  def __unicode__( self ):
    return 'Commit "%s" on branch "%s" of project "%s"' % ( self.commit, self.branch, self.project.name )

  class Meta:
      unique_together = ( 'project', 'commit', 'branch' )

  class API:
    not_allowed_methods = ( 'CREATE', 'DELETE', 'UPDATE', 'CALL' )
    constants = ( 'STATE_LIST', )
    properties = ( 'state', )
    list_filters = { 'project': { 'project': Project }, 'in_process': {} }

    @staticmethod
    def buildQS( qs, filter, values ):
      if filter == 'project':
        return qs.filter( project=values[ 'project' ] ).order_by( '-created' )

      if filter == 'in_process':
        return qs.filter( done_at__isnull=True )

      raise Exception( 'Invalid filter "%s"' % filter )


class Build( models.Model ):
  """
This is a type of Build that can be done
  """
  key = models.CharField( max_length=160, editable=False, primary_key=True ) # until djanog supports multi filed primary keys
  name = models.CharField( max_length=100 )
  project = models.ForeignKey( Project )
  dependancies = models.ManyToManyField( Package, through='BuildDependancy', help_text='' )
  resources = models.ManyToManyField( Resource, through='BuildResource', help_text='' )
  networks = models.TextField( default='{}' )
  manual = models.BooleanField()
  created = models.DateTimeField( editable=False, auto_now_add=True )
  updated = models.DateTimeField( editable=False, auto_now=True )

  def save( self, *args, **kwargs ):
    if not re.match( '^[a-z0-9][a-z0-9\-]*[a-z0-9]$', self.name ):
      raise ValidationError( 'Invalid name' )

    try:
      simplejson.loads( self.networks )
    except ValueError:
      raise ValidationError( 'networks must be valid JSON' )

    self.key = '%s_%s' % ( self.project.name, self.name )

    super( Build, self ).save( *args, **kwargs )

  def __unicode__( self ):
    return 'Build "%s" of "%s"' % ( self.name, self.project.name )

  class Meta:
      unique_together = ( 'name', 'project' )

  class API:
    not_allowed_methods = ( 'CREATE', 'DELETE', 'UPDATE', 'CALL' )
    list_filters = { 'project': { 'project': Project } }

    @staticmethod
    def buildQS( qs, filter, values ):
      if filter == 'project':
        return qs.filter( project=values[ 'project' ] )

      raise Exception( 'Invalid filter "%s"' % filter )


class BuildDependancy( models.Model ):
  key = models.CharField( max_length=250, editable=False, primary_key=True ) # until django supports multi filed primary keys
  build = models.ForeignKey( Build )
  package = models.ForeignKey( Package )
  state = models.CharField( max_length=RELEASE_TYPE_LENGTH, choices=RELEASE_TYPE_CHOICES )

  def save( self, *args, **kwargs ):
    self.key = '%s_%s' % ( self.build.key, self.package.name )

    super( BuildDependancy, self ).save( *args, **kwargs )

  def __unicode__( self ):
    return 'BuildDependancies from "%s" to "%s" at "%s"' % ( self.build.name, self.package.name, self.state )

  class Meta:
      unique_together = ( 'build', 'package' )

  class API:
    not_allowed_methods = ( 'CREATE', 'DELETE', 'UPDATE', 'CALL' )


class BuildResource( models.Model ):
  key = models.CharField( max_length=250, editable=False, primary_key=True ) # until djanog supports multi filed primary keys
  build = models.ForeignKey( Build )
  resource = models.ForeignKey( Resource )
  name = models.CharField( max_length=50 )
  quanity = models.IntegerField( default=1 )

  def save( self, *args, **kwargs ):
    self.key = '%s_%s_%s' % ( self.build.key, self.name, self.resource.name )

    super( BuildResource, self ).save( *args, **kwargs )

  def __unicode__( self ):
    return 'BuildResource from "%s" for "%s" named "%s"' % ( self.build.name, self.resource.name, self.name )

  class Meta:
      unique_together = ( 'build', 'name' )

  class API:
    not_allowed_methods = ( 'CREATE', 'DELETE', 'UPDATE', 'CALL' )
