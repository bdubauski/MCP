import re
import difflib

from django.utils import simplejson
from django.db import models
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.conf import settings

from mcp.lib.GitHub import GitHub
from mcp.Resource.models import Resource

# from packrat Repos/models.py
RELEASE_TYPE_LENGTH = 5
RELEASE_TYPE_CHOICES = ( ( 'ci', 'CI' ), ( 'dev', 'Development' ), ( 'stage', 'Staging' ), ( 'prod', 'Production' ), ( 'depr', 'Deprocated' ) )

def _markdownBlockQuote( lines ):
  return '>' + re.sub( r'([\\`\*_{}\+\-\.\!#\(\)\[\]])', r'\\\1', '\n>'.join( lines ) )

def _diffMarkDown( a, b ):
  result = ''
  sm = difflib.SequenceMatcher( None, a, b )
  for group in sm.get_grouped_opcodes( 3 ):
    for tag, i1, i2, j1, j2 in group:
      if tag == 'replace':
        result += '\n\n---\n\n_Changed %s:%s -> %s:%s_\n' % ( i1, i2, j1, j2 )
        result += _markdownBlockQuote( a[ i1:i2 ] )
        result += '\n\n_To %s:%s -> %s:%s_\n' % ( i1, i2, j1, j2 )
        result += _markdownBlockQuote( b[ j1:j2 ] )

      elif tag == 'delete':
        result += '\n\n---\n\n_Removed %s:%s -> %s:%s_\n' % ( i1, i2, j1, j2 )
        result += _markdownBlockQuote( a[ i1:i2 ] )

      elif tag == 'insert':
        result += '\n\n---\n\n_Added %s:%s -> %s:%s_\n' % ( i1, i2, j1, j2 )
        result += _markdownBlockQuote( b[ j1:j2 ] )

  if not result:
    return '\n_No Change_\n'
  else:
    return result

def _markdownResults( valueCur, valuePrev=None ):
  result = ''

  for target in ( 'lint', 'test', 'build' ):
    if target not in valueCur:
      continue

    result += '%s Results:\n\n' % target.title()
    try:
      tmp_target = valuePrev[ target ]
    except ( TypeError, KeyError ):
      tmp_target = None

    for group in valueCur[ target ]:
      try:
        tmp_group = tmp_target[ group ]
      except ( TypeError, KeyError ):
        tmp_group = None

      if isinstance( valueCur[ target ][ group ], dict ):
        for subgroup in valueCur[ target ][ group ]:
          try:
            tmp_subgroup = tmp_group[ subgroup ]
          except ( TypeError, KeyError ):
            tmp_subgroup = None

          lines = valueCur[ target ][ group ][ subgroup ][1].splitlines()

          result += '**%s** - **%s**\n' % ( group, subgroup )
          if tmp_subgroup is None:
            result += '  Success: **%s**\n' % valueCur[ target ][ group ][ subgroup ][0]
            result += _markdownBlockQuote( lines )

          else:
            result += '  Success: **%s** -> **%s**\n' % ( tmp_subgroup[0], valueCur[ target ][ group ][ subgroup ][0] )
            result += _diffMarkDown( tmp_subgroup[1].splitlines(), lines )

      else:
        lines = valueCur[ target ][ group ][1].splitlines()

        result += '**%s**\n' % group
        if tmp_group is None:
          result += '  Success: **%s**\n' % valueCur[ target ][ group ][0]
          result += _markdownBlockQuote( lines )

        else:
          result += '  Success: **%s** -> **%s**\n' % ( tmp_group[0], valueCur[ target ][ group ][0] )
          result += _diffMarkDown( tmp_group[1].splitlines(), lines )

      result += '\n\n'

  return result

class Project( models.Model ):
  """
This is a Generic Project
  """
  name = models.CharField( max_length=50, primary_key=True )
  local_path = models.CharField( max_length=150, null=True, blank=True, editable=False )
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
    list_filters = { 'my_projects': {} }

    @staticmethod
    def buildQS( qs, user, filter, values ):
      if filter == 'my_projects':
        if user.is_anonymous():
          return qs

        return qs.filter( project__in=user.projects.all().order_by( 'name' ).values_list( 'name', flat=True ) )

      raise Exception( 'Invalid filter "%s"' % filter )

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
  package = models.ForeignKey( Package, on_delete=models.CASCADE )
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
  project = models.ForeignKey( Project, on_delete=models.CASCADE )
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

  @property
  def summary( self ):
    if self.passed is None and self.built is None:
      return None

    result = []

    if self.passed is True:
      result.append( 'Passed: True' )
    elif self.passed is False:
      result.append( 'Passed: False' )

    if self.built is True:
      result.append( 'Built: True' )
    elif self.built is False:
      result.append( 'Built: False' )

    return '\n'.join( result )

  @property
  def results( self ): # for now in Markdown format
    result = {}

    if self.lint_results:
      tmp = simplejson.loads( self.lint_results )
      wrk = {}
      for distro in tmp:
        if tmp[ distro ].get( 'results', None ) is not None:
          wrk[ distro ] = ( tmp[ distro ].get( 'success', False ), tmp[ distro ][ 'results' ] )

      if wrk:
        result[ 'lint' ] = wrk

    if self.test_results:
      tmp = simplejson.loads( self.test_results )
      wrk = {}
      for distro in tmp:
        if tmp[ distro ].get( 'results', None ) is not None:
          wrk[ distro ] = ( tmp[ distro ].get( 'success', False ), tmp[ distro ][ 'results' ] )

      if wrk:
        result[ 'test' ] = wrk

    if self.build_results:
      tmp = simplejson.loads( self.build_results )
      wrk = {}
      for target in tmp:
        wrk[ target ] = {}
        for distro in tmp[ target ]:
          if tmp[ target ][ distro ].get( 'results', None ) is not None:
            wrk[ target ][ distro ] = ( tmp[ target ][ distro ].get( 'success', False ), tmp[ target ][ distro ][ 'results' ] )

      if wrk:
        result[ 'build' ] = wrk

    if not result:
      return None
    else:
      return result

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

    if not self.branch.startswith( '_PR' ):
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

    comment = self.results

    try:
      prev_comment = Commit.objects.filter( project=self.project, branch=self.branch, done_at__lt=self.done_at ).order_by( '-done_at' )[0].results
    except ( Commit.DoesNotExist, IndexError ):
      prev_comment = None

    if prev_comment is None and comment is None:
      comment = '**Nothing To Do**'
    elif prev_comment is not None and comment is None:
      comment = '**Last Commit Had Results, This One Did Not**'
    else:
      comment = _markdownResults( comment, prev_comment )

    gh.postCommitComment( self.commit, comment )

    if self.branch.startswith( '_PR' ):
      summary = self.summary

      if summary is None:
        summary = '**Nothing To Do**'

      if self.passed is None and self.built is None:
        gh.postCommitStatus( self.commit, 'success', description='No Test/Lint/Build to do' )
      elif self.built is False:
        gh.postCommitStatus( self.commit, 'error', description='Package Build Error' )
      elif self.passed is False:
        gh.postCommitStatus( self.commit, 'failure', description='Test/Lint Failure' )
      elif self.passed is True:
        gh.postCommitStatus( self.commit, 'success', description='Test/Lint Passed' )

      gh.setOwner()

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
    def buildQS( qs, user, filter, values ):
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
  project = models.ForeignKey( Project, on_delete=models.CASCADE )
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
    def buildQS( qs, user, filter, values ):
      if filter == 'project':
        return qs.filter( project=values[ 'project' ] )

      raise Exception( 'Invalid filter "%s"' % filter )


class BuildDependancy( models.Model ):
  key = models.CharField( max_length=250, editable=False, primary_key=True ) # until django supports multi filed primary keys
  build = models.ForeignKey( Build, on_delete=models.CASCADE )
  package = models.ForeignKey( Package, on_delete=models.CASCADE )
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
  build = models.ForeignKey( Build, on_delete=models.CASCADE )
  resource = models.ForeignKey( Resource, on_delete=models.CASCADE )
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
