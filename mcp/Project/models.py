import re
import difflib

from django.db import models
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.conf import settings

from cinp.orm_django import DjangoCInP as CInP

from mcp.fields import MapField, name_regex
from mcp.lib.GitHub import GitHub
from mcp.Resource.models import Resource


cinp = CInP( 'Project', '0.1' )


COMMIT_STATE_LIST = ( 'new', 'linted', 'tested', 'built', 'doced', 'done' )


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
        result += '\n\n---\n\n_Changed {0}:{1} -> {2}:{3}_\n'.format( i1, i2, j1, j2 )
        result += _markdownBlockQuote( a[ i1:i2 ] )
        result += '\n\n_To {0}:{1} -> {2}:{3}_\n'.format( i1, i2, j1, j2 )
        result += _markdownBlockQuote( b[ j1:j2 ] )

      elif tag == 'delete':
        result += '\n\n---\n\n_Removed {0}:{1} -> {2}:{3}s_\n'.format( i1, i2, j1, j2 )
        result += _markdownBlockQuote( a[ i1:i2 ] )

      elif tag == 'insert':
        result += '\n\n---\n\n_Added {0}:{1} -> {2}:{3}_\n'.format( i1, i2, j1, j2 )
        result += _markdownBlockQuote( b[ j1:j2 ] )

  if not result:
    return '\n_No Change_\n'
  else:
    return result


def _markdownResults( valueCur, valuePrev=None ):
  result = ''

  for target in ( 'lint', 'test', 'build', 'docs' ):
    if target not in valueCur:
      continue

    result += '{0} Results:\n\n'.format( target.title() )
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

          result += '**{0}** - **{1}**\n'.format( group, subgroup )
          if tmp_subgroup is None:
            result += '  Success: **{0}**\n'.format( valueCur[ target ][ group ][ subgroup ][0] )
            if valueCur[ target ][ group ][ subgroup ][2] is not None:
              result += '  Score: **{0}**\n'.format( valueCur[ target ][ group ][ subgroup ][2] )
            result += _markdownBlockQuote( lines )

          else:
            result += '  Success: **{0}** -> **{1}**\n'.format( tmp_subgroup[0], valueCur[ target ][ group ][ subgroup ][0] )
            if valueCur[ target ][ group ][ subgroup ][2] is not None:
              result += '  Success: **{0}** -> **{1}**\n'.format( tmp_subgroup[2], valueCur[ target ][ group ][ subgroup ][2] )
            result += _diffMarkDown( tmp_subgroup[1].splitlines(), lines )

      else:
        lines = valueCur[ target ][ group ][1].splitlines()

        result += '**{0}**\n'.format( group )
        if tmp_group is None:
          result += '  Success: **{0}**\n'.format( valueCur[ target ][ group ][0] )
          if valueCur[ target ][ group ][2] is not None:
            result += '  Score: **{0}**\n'.format( valueCur[ target ][ group ][2] )
          result += _markdownBlockQuote( lines )

        else:
          result += '  Success: **{0}** -> **{1}**\n'.format( tmp_group[0], valueCur[ target ][ group ][0] )
          if valueCur[ target ][ group ][2] is not None:
            result += '  Score: **{0}** -> **{1}**\n'.format( tmp_group[2], valueCur[ target ][ group ][2] )
            try:
              if float( tmp_group[2] > float( valueCur[ target ][ group ][2] ) ):
                result += '## WARNING: Score value decreased ##'
            except ValueError:
              pass
          result += _diffMarkDown( tmp_group[1].splitlines(), lines )

      result += '\n\n'

  return result


@cinp.model( not_allowed_verb_list=[ 'CREATE', 'DELETE', 'UPDATE', 'CALL' ], hide_field_list=[ 'local_path' ], property_list=[ 'type', 'org', 'repo', 'busy', 'upstream_git_url', 'internal_git_url', 'status' ] )
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
  def busy( self ):  # ie. can it be updated, and scaned for new things to do
    not_busy = True
    for build in self.build_set.all():
      for item in build.queueitem_set.all():
        not_busy &= item.manual

      for job in build.buildjob_set.all():
        not_busy &= job.manual

    return not not_busy

  @property
  def internal_git_url( self ):
    return '{0}{1}'.format( settings.GIT_HOST, self.local_path )

  @property
  def upstream_git_url( self ):
    try:  # for now we only support git based projects
      return '{0}/{1}/{2}.git'.format( settings.GITHUB_HOST, self.githubproject.org, self.githubproject.repo )
    except ObjectDoesNotExist:
      pass

    try:
      return self.gitproject.git_url
    except ObjectDoesNotExist:
      pass

    return None

  @property
  def clone_git_url( self ):
    if settings.GITHUB_PASS is not None:
      auth = '{0}:{1}'.format( settings.GITHUB_USER, settings.GITHUB_PASS )
    else:
      auth = settings.GITHUB_USER

    try:  # for now we only support git based projects
      return ( '{0}{1}/{2}.git'.format( settings.GITHUB_HOST, self.githubproject.org, self.githubproject.repo ) ).replace( '://', '://{0}@'.format( auth ) )
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

  @cinp.list_filter( name='my_projects', paramater_type_list=[ { 'type': '_USER_' } ] )
  @staticmethod
  def filter_my_projects( user ):
    if user.is_anonymous():
      return Project.objects.all()

    return Project.objects.filter( project__in=user.projects.all().order_by( 'name' ).values_list( 'name', flat=True ) )

  @cinp.check_auth()
  @staticmethod
  def checkAuth( user, verb, id_list, action=None ):
    return True

  def clean( self, *args, **kwargs ):
    super().clean( *args, **kwargs )

    if not self.local_path:
      self.local_path = None

    errors = {}

    if not name_regex.match( self.name ):
      errors[ 'name' ] = 'Invalid'

    if errors:
      raise ValidationError( errors )

  def __str__( self ):
    return 'Project "{0}"'.format( self.name )


@cinp.model( not_allowed_verb_list=[ 'CALL' ] )
class GitProject( Project ):
  """
This is a Git Project
  """
  git_url = models.CharField( max_length=200 )

  @cinp.check_auth()
  @staticmethod
  def checkAuth( user, verb, id_list, action=None ):
    return True

  def __str__( self ):
    return 'Git Project "{0}"'.format( self.name )


@cinp.model( not_allowed_verb_list=[ 'CALL' ] )
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

  @cinp.check_auth()
  @staticmethod
  def checkAuth( user, verb, id_list, action=None ):
    return True

  def __str__( self ):
    return 'GitHub Project "{0}"({1}/{2})'.format( self.name, self._org, self._repo )


@cinp.model( not_allowed_verb_list=[ 'CREATE', 'DELETE', 'UPDATE', 'CALL' ] )
class Package( models.Model ):
  """
This is a Package
  """
  name = models.CharField( max_length=100, primary_key=True )
  created = models.DateTimeField( editable=False, auto_now_add=True )
  updated = models.DateTimeField( editable=False, auto_now=True )

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
    return 'Package "{0}"'.format( self.name )


@cinp.model( not_allowed_verb_list=[ 'CREATE', 'DELETE', 'UPDATE', 'CALL' ] )
class PackageVersion( models.Model ):
  """
This is a Version of a Package
  """
  package = models.ForeignKey( Package, on_delete=models.CASCADE )
  version = models.CharField( max_length=50 )
  state = models.CharField( max_length=RELEASE_TYPE_LENGTH, choices=RELEASE_TYPE_CHOICES )
  created = models.DateTimeField( editable=False, auto_now_add=True )
  updated = models.DateTimeField( editable=False, auto_now=True )

  @cinp.check_auth()
  @staticmethod
  def checkAuth( user, verb, id_list, action=None ):
    return True

  def __str__( self ):
    return 'PackageVersion "{0}" verison "{1}"'.format( self.package.name, self.version )

  class Meta:
    unique_together = ( 'package', 'version' )


@cinp.model( not_allowed_verb_list=[ 'CREATE', 'DELETE', 'UPDATE', 'CALL' ], property_list=[ { 'name': 'state', 'choices': COMMIT_STATE_LIST } ] )
class Commit( models.Model ):
  """
A Single Commit of a Project
  """
  project = models.ForeignKey( Project, on_delete=models.CASCADE )
  owner_override = models.CharField( max_length=50, blank=True, null=True )
  branch = models.CharField( max_length=50 )
  commit = models.CharField( max_length=45 )
  lint_results = MapField( blank=True )
  test_results = MapField( blank=True )
  build_results = MapField( blank=True )
  docs_results = MapField( blank=True )
  lint_at = models.DateTimeField( editable=False, blank=True, null=True )
  test_at = models.DateTimeField( editable=False, blank=True, null=True )
  build_at = models.DateTimeField( editable=False, blank=True, null=True )
  docs_at = models.DateTimeField( editable=False, blank=True, null=True )
  done_at = models.DateTimeField( editable=False, blank=True, null=True )
  passed = models.NullBooleanField( editable=False, blank=True, null=True )
  built = models.NullBooleanField( editable=False, blank=True, null=True )
  created = models.DateTimeField( editable=False, auto_now_add=True )
  updated = models.DateTimeField( editable=False, auto_now=True )

  @property
  def state( self ):
    if self.done_at and self.doced_at and self.build_at and self.test_at and self.lint_at:
      return 'done'

    if self.doced_at and self.build_at and self.test_at and self.lint_at:
      return 'doced'

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
  def results( self ):  # for now in Markdown format
    result = {}

    wrk = {}
    for distro in self.lint_results:
      tmp = self.lint_results[ distro ]
      if tmp.get( 'results', None ) is not None:
        wrk[ distro ] = ( tmp.get( 'success', False ), tmp[ 'results' ], tmp.get( 'score', None ) )

    if wrk:
      result[ 'lint' ] = wrk

    wrk = {}
    for distro in self.test_results:
      tmp = self.test_results[ distro ]
      if tmp.get( 'results', None ) is not None:
        wrk[ distro ] = ( tmp.get( 'success', False ), tmp[ 'results' ], tmp.get( 'score', None ) )

    if wrk:
      result[ 'test' ] = wrk

    wrk = {}
    for target in self.build_results:
      wrk[ target ] = {}
      tmp = self.build_results[ target ]
      for distro in tmp[ target ]:
        if tmp[ distro ].get( 'results', None ) is not None:
          wrk[ target ][ distro ] = ( tmp[ distro ].get( 'success', False ), tmp[ distro ][ 'results' ], tmp[ distro ].get( 'score', None ) )

    if wrk:
      result[ 'build' ] = wrk

    wrk = {}
    for distro in self.docs_results:
      tmp = self.docs_results[ distro ]
      if tmp.get( 'results', None ) is not None:
        wrk[ distro ] = ( tmp.get( 'success', False ), tmp[ 'results' ], tmp.get( 'score', None ) )

    if wrk:
      result[ 'docs' ] = wrk

    if not result:
      return None

    else:
      return result

  def signalComplete( self, target, build_name, resources ):
    if target not in ( 'lint', 'test', 'rpm', 'dpkg', 'respkg', 'resource', 'docs' ):
      return

    sucess = resources[ 'target' ][0].get( 'success', False )
    results = resources[ 'target' ][0].get( 'results', None )

    if target == 'lint':
      self.lint_results[ build_name ][ 'status' ] = 'done'
      self.lint_results[ build_name ][ 'success' ] = sucess
      self.lint_results[ build_name ][ 'results' ] = results

    elif target == 'test':
      self.test_results[ build_name ][ 'status' ] = 'done'
      self.test_results[ build_name ][ 'success' ] = sucess
      self.test_results[ build_name ][ 'results' ] = results

    elif target == 'docs':
      self.docs_results[ build_name ][ 'status' ] = 'done'
      self.docs_results[ build_name ][ 'success' ] = sucess
      self.docs_results[ build_name ][ 'results' ] = results

    else:
      self.build_results[ target ][ build_name ][ 'status' ] = 'done'
      self.build_results[ target ][ build_name ][ 'success' ] = sucess
      self.build_results[ target ][ build_name ][ 'results' ] = results

    self.full_clean()
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

  @cinp.list_filter( name='project', paramater_type_list=[ { 'type': 'Model', 'model': Project } ] )
  @staticmethod
  def filter_project( project ):
    return Commit.objects.objects.filter( project=project ).order_by( '-created' )

  @cinp.list_filter( name='in_process', paramater_type_list=[] )
  @staticmethod
  def filter_in_process():
    return Commit.objects.objects.filter( done_at__isnull=True )

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
    return 'Commit "{0}" on branch "{1}" of project "{2}"'.format( self.commit, self.branch, self.project.name )


@cinp.model( not_allowed_verb_list=[ 'CREATE', 'DELETE', 'UPDATE', 'CALL' ] )
class Build( models.Model ):
  """
This is a type of Build that can be done
  """
  key = models.CharField( max_length=160, editable=False, primary_key=True )  # until djanog supports multi filed primary keys
  name = models.CharField( max_length=100 )
  project = models.ForeignKey( Project, on_delete=models.CASCADE )
  dependancies = models.ManyToManyField( Package, through='BuildDependancy', help_text='' )
  resources = models.ManyToManyField( Resource, through='BuildResource', help_text='' )
  network_map = MapField( blank=True )
  manual = models.BooleanField()
  created = models.DateTimeField( editable=False, auto_now_add=True )
  updated = models.DateTimeField( editable=False, auto_now=True )

  @cinp.list_filter( name='project', paramater_type_list=[ { 'type': 'Model', 'model': Project } ] )
  @staticmethod
  def filter_project( project ):
    return Build.objects.objects.filter( project=project )

  @cinp.check_auth()
  @staticmethod
  def checkAuth( user, verb, id_list, action=None ):
    return True

  def clean( self, *args, **kwargs ):
    super().clean( *args, **kwargs )
    self.key = '{0}_{1}'.format( self.project.name, self.name )

    errors = {}

    if not name_regex.match( self.name ):
      errors[ 'name' ] = 'Invalid'

    if errors:
      raise ValidationError( errors )

  def __str__( self ):
    return 'Build "{0}" of "{1}"'.format( self.name, self.project.name )

  class Meta:
    unique_together = ( 'name', 'project' )


@cinp.model( not_allowed_verb_list=[ 'CREATE', 'DELETE', 'UPDATE', 'CALL' ] )
class BuildDependancy( models.Model ):
  key = models.CharField( max_length=250, editable=False, primary_key=True )  # until django supports multi filed primary keys
  build = models.ForeignKey( Build, on_delete=models.CASCADE )
  package = models.ForeignKey( Package, on_delete=models.CASCADE )
  state = models.CharField( max_length=RELEASE_TYPE_LENGTH, choices=RELEASE_TYPE_CHOICES )

  @cinp.check_auth()
  @staticmethod
  def checkAuth( user, verb, id_list, action=None ):
    return True

  def clean( self, *args, **kwargs ):
    super().clean( *args, **kwargs )
    self.key = '{0}_{1}'.format( self.build.key, self.package.name )

    errors = {}

    if errors:
      raise ValidationError( errors )

  def __str__( self ):
    return 'BuildDependancies from "{0}" to "{1}" at "{2}"'.format( self.build.name, self.package.name, self.state )

  class Meta:
    unique_together = ( 'build', 'package' )


@cinp.model( not_allowed_verb_list=[ 'CREATE', 'DELETE', 'UPDATE', 'CALL' ] )
class BuildResource( models.Model ):
  key = models.CharField( max_length=250, editable=False, primary_key=True )  # until djanog supports multi filed primary keys
  build = models.ForeignKey( Build, on_delete=models.CASCADE )
  resource = models.ForeignKey( Resource, on_delete=models.CASCADE )
  name = models.CharField( max_length=50 )
  quanity = models.IntegerField( default=1 )

  @cinp.check_auth()
  @staticmethod
  def checkAuth( user, verb, id_list, action=None ):
    return True

  def clean( self, *args, **kwargs ):
    super().clean( *args, **kwargs )
    self.key = '{0}_{1}_{2}'.format( self.build.key, self.name, self.resource.name )

    errors = {}

    if errors:
      raise ValidationError( errors )

  def __str__( self ):
    return 'BuildResource from "{0}" for "{1}" named "{2}"'.format( self.build.name, self.resource.name, self.name )

  class Meta:
    unique_together = ( 'build', 'name' )
