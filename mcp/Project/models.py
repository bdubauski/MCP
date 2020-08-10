import re
import os
import difflib
from datetime import datetime

from django.db import models
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.conf import settings

from cinp.orm_django import DjangoCInP as CInP

from mcp.fields import MapField, name_regex, package_filename_regex, packagefile_regex, TAG_NAME_LENGTH, PACKAGE_FILENAME_LENGTH, BLUEPRINT_NAME_LENGTH
from mcp.lib.InternalGit import InternalGit
from mcp.lib.Git import Git
from mcp.lib.GitHub import GitHub
from mcp.lib.GitLab import GitLab
from mcp.Resource.models import Resource


cinp = CInP( 'Project', '0.1' )


COMMIT_STATE_LIST = ( 'new', 'tested', 'built', 'doced', 'done' )


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

  for target in ( 'lint', 'test', 'build', 'doc' ):
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
              if float( tmp_group[2] ) > float( valueCur[ target ][ group ][2] ):
                result += '## WARNING: Score value decreased ##'
            except ( ValueError, TypeError ):
              pass
          result += _diffMarkDown( tmp_group[1].splitlines(), lines )

      result += '\n\n'

  return result


def _commitSumary2Str( summary ):
  if not summary:
    return '**Nothing To Do**'

  if 'doc' in summary:
    return 'Lint: {0} {1}\nTest: {2} {3}\nBuild: {4}\nDoc: {5}\nOverall: {6}\n'.format(
                                                                                         summary[ 'lint' ][ 'status' ],
                                                                                         '({0})'.format( summary[ 'lint' ][ 'score' ] ) if summary[ 'lint' ][ 'score' ] else '',
                                                                                         summary[ 'test' ][ 'status' ],
                                                                                         '({0})'.format( summary[ 'test' ][ 'score' ] ) if summary[ 'test' ][ 'score' ] else '',
                                                                                         summary[ 'build' ][ 'status' ],
                                                                                         summary[ 'doc' ][ 'status' ],
                                                                                         summary[ 'status' ] )
  else:
    return 'Lint: {0} {1}\nTest: {2} {3}\nBuild: {4}\nOverall: {5}\n'.format(
                                                                               summary[ 'lint' ][ 'status' ],
                                                                               '({0})'.format( summary[ 'lint' ][ 'score' ] ) if summary[ 'lint' ][ 'score' ] else '',
                                                                               summary[ 'test' ][ 'status' ],
                                                                               '({0})'.format( summary[ 'test' ][ 'score' ] ) if summary[ 'test' ][ 'score' ] else '',
                                                                               summary[ 'build' ][ 'status' ],
                                                                               summary[ 'status' ] )


@cinp.model( not_allowed_verb_list=[ 'CREATE', 'DELETE', 'UPDATE', 'CALL' ], hide_field_list=[ 'local_path' ], property_list=[ 'type', { 'name': 'busy', 'type': 'Boolean' }, 'upstream_git_url', 'internal_git_url', { 'name': 'status', 'type': 'Map' } ], read_only_list=[ 'last_checked', 'build_counter' ] )
class Project( models.Model ):
  """
This is a Generic Project
  """
  name = models.CharField( max_length=50, primary_key=True )
  release_branch = models.CharField( max_length=100, default='master' )
  local_path = models.CharField( max_length=150, null=True, blank=True, editable=False )
  build_counter = models.IntegerField( default=0 )
  last_checked = models.DateTimeField( default=datetime.min )
  created = models.DateTimeField( editable=False, auto_now_add=True )
  updated = models.DateTimeField( editable=False, auto_now=True )

  @property
  def type( self ):
    try:
      self.githubproject
      return 'GitHubProject'
    except ObjectDoesNotExist:
      pass

    try:
      self.gitlabproject
      return 'GitLabProject'
    except ObjectDoesNotExist:
      pass

    try:
      self.gitproject
      return 'GitProject'
    except ObjectDoesNotExist:
      pass

    return 'Project'

  @property
  def scm( self ):
    try:
      return self.githubproject.scm
    except ObjectDoesNotExist:
      pass

    try:
      return self.gitlabproject.scm
    except ObjectDoesNotExist:
      pass

    try:
      return self.gitproject.scm
    except ObjectDoesNotExist:
      pass

    return None

  @property
  def internal_git( self ):
    return InternalGit( os.path.join( settings.GIT_LOCAL_PATH, self.local_path ), self.release_branch )

  @property
  def busy( self ):
    # have any commits in flight
    if self.commit_set.filter( done_at__isnull=True ).count() > 0:
      return True

    # have any queue items
    if self.queueitem_set.count() > 0:
      return True

    # have manual jobs that have not run
    # or auto jobs that have not reported
    for job in self.buildjob_set.all():
      if job.manual:
        if job.state not in ( 'ran', 'reported', 'acknowledged', 'released' ):
          return True
      else:
        if job.state not in ( 'reported', 'acknowledged', 'released' ):
          return True

    return False

  @property
  def internal_git_url( self ):  # for hading out to nullunit, ie: the one hosted by MCP
    return '{0}{1}'.format( settings.GIT_HOST, self.local_path )

  @property
  def upstream_git_url( self ):  # a helpfull link for users clone to the project from the upstream SCM
    if self.type == 'GitHubProject':
      return '{0}/{1}/{2}.git'.format( settings.GITHUB_HOST, self.githubproject.github_org, self.githubproject.github_repo )

    elif self.type == 'GitLabProject':
      return '{0}/{1}/{2}.git'.format( settings.GITLAB_HOST, self.gitlabproject.gitlab_group_id, self.gitlabproject.gitlab_project_id )

    elif self.type == 'GitProject':
      return self.gitproject.git_repo

    return None

  @property
  def clone_git_url( self ):  # url used by rinzler to clone the repo
    if self.type == 'GitHubProject':
      if settings.GITHUB_PASS is not None:
        auth = '{0}:{1}'.format( settings.GITHUB_USER, settings.GITHUB_PASS )
      else:
        auth = settings.GITHUB_USER

      return ( '{0}{1}/{2}.git'.format( settings.GITHUB_HOST, self.githubproject.github_org, self.githubproject.github_repo ) ).replace( '://', '://{0}@'.format( auth ) )

    elif self.type == 'GitLabProject':
      if settings.GITLAB_PASS is not None:
        auth = '{0}:{1}'.format( settings.GITLAB_USER, settings.GITLAB_PASS )
      else:
        auth = settings.GITLAB_USER

      return ( '{0}{1}/{2}.git'.format( settings.GITLAB_HOST, self.githubproject.gitlab_group_id, self.githubproject.gitlab_project_id ) ).replace( '://', '://{0}@'.format( auth ) )

    elif self.type == 'GitProject':
      return self.gitproject.git_repo

    return None

  @property
  def status( self ):
    try:
      commit = self.commit_set.filter( branch=self.release_branch, done_at__isnull=False ).order_by( '-created' )[0]
    except IndexError:
      return { 'test': None, 'build': None, 'doc': None, 'at': None }

    summary = commit.summary

    return { 'test': summary[ 'test' ][ 'status' ], 'build': summary[ 'build' ][ 'status' ], 'doc': summary[ 'doc' ][ 'status' ], 'at': commit.created.isoformat() }

  @cinp.list_filter( name='my_projects' )
  @staticmethod
  def filter_my_projects():
    return Project.objects.all()

  # @cinp.list_filter( name='my_projects', paramater_type_list=[ { 'type': '_USER_' } ] )
  # @staticmethod
  # def filter_my_projects( user ):
  #   if user.is_anonymous():
  #     return Project.objects.all()
  #
  #   return Project.objects.filter( project__in=user.projects.all().order_by( 'name' ).values_list( 'name', flat=True ) )

  @cinp.check_auth()
  @staticmethod
  def checkAuth( user, verb, id_list, action=None ):
    return True

  def clean( self, *args, **kwargs ):
    super().clean( *args, **kwargs )

    if not self.local_path:
      self.local_path = None

    errors = {}

    if self.name != '_builtin_' and not name_regex.match( self.name ):
      errors[ 'name' ] = 'Invalid'

    if errors:
      raise ValidationError( errors )

  def __str__( self ):
    return 'Project "{0}"'.format( self.name )


@cinp.model( not_allowed_verb_list=[ 'CALL' ], read_only_list=[ 'last_checked', 'build_counter' ] )
class GitProject( Project ):
  """
This is a Git Project
  """
  git_repo = models.CharField( max_length=200 )

  @property
  def type( self ):
    return 'GitProject'

  @property
  def scm( self ):
    return Git( self.git_repo )

  @cinp.check_auth()
  @staticmethod
  def checkAuth( user, verb, id_list, action=None ):
    return True

  def __str__( self ):
    return 'Git Project "{0}"'.format( self.name )


@cinp.model( not_allowed_verb_list=[ 'CALL' ], read_only_list=[ 'last_checked', 'build_counter' ] )
class GitHubProject( Project ):
  """
This is a GitHub Project
  """
  github_org = models.CharField( max_length=50 )
  github_repo = models.CharField( max_length=50 )

  @property
  def type( self ):
    return 'GitHubProject'

  @property
  def scm( self ):
    try:
      if self._github:
        return self._github
    except AttributeError:
      pass

    self._github = GitHub( settings.GITHUB_API_HOST, settings.GITHUB_PROXY, settings.GITHUB_USER, settings.GITHUB_PASS, self.github_org, self.github_repo )
    return self._github

  @cinp.check_auth()
  @staticmethod
  def checkAuth( user, verb, id_list, action=None ):
    return True

  def __str__( self ):
    return 'GitHub Project "{0}"({1}/{2})'.format( self.name, self._org, self._repo )


@cinp.model( not_allowed_verb_list=[ 'CALL' ], read_only_list=[ 'last_checked', 'build_counter' ] )
class GitLabProject( Project ):
  """
This is a GitLab Project
  """
  gitlab_group_id = models.IntegerField()
  gitlab_project_id = models.IntegerField()

  @property
  def type( self ):
    return 'GitLabProject'

  @property
  def scm( self ):
    try:
      if self._gitlab:
        return self._gitlab
    except AttributeError:
      pass

    self._gitlab = GitLab( settings.GITLAB_API_HOST, settings.GITLAB_PROXY, settings.GITLAB_USER, settings.GITLAB_PASS, self.group_id, self.project_id )
    return self._gitlab

  @cinp.check_auth()
  @staticmethod
  def checkAuth( user, verb, id_list, action=None ):
    return True

  def __str__( self ):
    return 'GitLab Project "{0}"({1}/{2})'.format( self.name, self._group_id, self._project_id )


@cinp.model( not_allowed_verb_list=[ 'CREATE', 'DELETE', 'UPDATE', 'CALL' ] )
class Package( models.Model ):
  """
This is a Package
  """
  name = models.CharField( max_length=100, primary_key=True )
  packrat_id = models.CharField( max_length=100, unique=True )
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


@cinp.model( not_allowed_verb_list=[ 'CREATE', 'DELETE', 'UPDATE', 'CALL' ], property_list=[ { 'name': 'state', 'choices': COMMIT_STATE_LIST }, { 'name': 'summary', 'type': 'Map' } ] )
class Commit( models.Model ):
  """
A Single Commit of a Project
  """
  project = models.ForeignKey( Project, on_delete=models.CASCADE )
  branch = models.CharField( max_length=50 )
  commit = models.CharField( max_length=45 )
  version = models.CharField( max_length=50, blank=True, null=True )
  lint_results = MapField( blank=True )
  test_results = MapField( blank=True )
  build_results = MapField( blank=True )
  doc_results = MapField( blank=True )
  test_at = models.DateTimeField( editable=False, blank=True, null=True )
  build_at = models.DateTimeField( editable=False, blank=True, null=True )
  doc_at = models.DateTimeField( editable=False, blank=True, null=True )
  done_at = models.DateTimeField( editable=False, blank=True, null=True )
  package_file_map = MapField( blank=True )
  created = models.DateTimeField( editable=False, auto_now_add=True )
  updated = models.DateTimeField( editable=False, auto_now=True )

  @property
  def state( self ):
    if self.done_at and self.doc_at and self.build_at and self.test_at:
      return 'done'

    if self.doc_at and self.build_at and self.test_at:
      return 'doced'

    if self.build_at and self.test_at:
      return 'built'

    if self.test_at:
      return 'tested'

    return 'new'

  @property
  def summary( self ):
    result = { 'test': {}, 'lint': {} }

    overall_complete = True
    overall_success = True

    score_list = []
    complete = True
    success = True
    for ( name, value ) in self.lint_results.items():
      if value.get( 'score', None ) is not None:
        score_list.append( value[ 'score' ]  )

      complete &= value.get( 'status', '' ) == 'done'
      success &= value.get( 'success', False )

    if score_list:
      result[ 'lint' ][ 'score' ] = sum( score_list ) / len( score_list )
    else:
      result[ 'lint' ][ 'score' ] = None

    if not complete:
      result[ 'lint' ][ 'status' ] = 'Incomplete'
    elif success:
      result[ 'lint' ][ 'status' ] = 'Success'
    else:
      result[ 'lint' ][ 'status' ] = 'Failed'

    overall_complete &= complete
    overall_success &= success

    score_list = []
    complete = True
    success = True
    for ( name, value ) in self.test_results.items():
      if value.get( 'score', None ) is not None:
        try:
          score_list.append( float( value[ 'score' ] ) )
        except ValueError:
          score_list.append( 0.0 )

      complete &= value.get( 'status', '' ) == 'done'
      success &= value.get( 'success', False )

    if score_list:
      result[ 'test' ][ 'score' ] = sum( score_list ) / len( score_list )
    else:
      result[ 'test' ][ 'score' ] = None

    if not complete:
      result[ 'test' ][ 'status' ] = 'Incomplete'
    elif success:
      result[ 'test' ][ 'status' ] = 'Success'
    else:
      result[ 'test' ][ 'status' ] = 'Failed'

    overall_complete &= complete
    overall_success &= success

    complete = True
    success = True
    for target in self.build_results:
      for( name, value ) in self.build_results[ target ].items():
        complete &= value.get( 'status', '' ) == 'done'
        success &= value.get( 'success', False )

    result[ 'build' ] = {}
    if not complete:
      result[ 'build' ][ 'status' ] = 'Incomplete'
    elif success:
      result[ 'build' ][ 'status' ] = 'Success'
    else:
      result[ 'build' ][ 'status' ] = 'Failed'

    overall_complete &= complete
    overall_success &= success

    if self.branch == self.project.release_branch:
      complete = True
      success = True
      for ( name, value ) in self.doc_results.items():
        complete &= value.get( 'status', '' ) == 'done'
        success &= value.get( 'success', False )

      result[ 'doc' ] = {}
      if not complete:
        result[ 'doc' ][ 'status' ] = 'Incomplete'
      elif success:
        result[ 'doc' ][ 'status' ] = 'Success'
      else:
        result[ 'doc' ][ 'status' ] = 'Failed'

    overall_complete &= complete
    overall_success &= success

    if not overall_success:
      result[ 'status' ] = 'Failed'
    elif not overall_complete:
      result[ 'status' ] = 'Incomplete'
    else:
      result[ 'status' ] = 'Success'

    return result

  @property
  def results( self ):  # for now in Markdown format
    result = {}

    wrk = {}
    for name in self.lint_results:
      tmp = self.lint_results[ name ]
      if tmp.get( 'results', None ) is not None:
        wrk[ name ] = ( tmp.get( 'success', False ), tmp[ 'results' ], tmp.get( 'score', None ) )

    if wrk:
      result[ 'lint' ] = wrk

    wrk = {}
    for name in self.test_results:
      tmp = self.test_results[ name ]
      if tmp.get( 'results', None ) is not None:
        wrk[ name ] = ( tmp.get( 'success', False ), tmp[ 'results' ], tmp.get( 'score', None ) )

    if wrk:
      result[ 'test' ] = wrk

    wrk = {}
    for target in self.build_results:
      wrk[ target ] = {}
      tmp = self.build_results[ target ]
      for name in tmp:
        if tmp[ name ].get( 'results', None ) is not None:
          wrk[ target ][ name ] = ( tmp[ name ].get( 'success', False ), tmp[ name ][ 'results' ], None )

    if wrk:
      result[ 'build' ] = wrk

    wrk = {}
    for name in self.doc_results:
      tmp = self.doc_results[ name ]
      if tmp.get( 'results', None ) is not None:
        wrk[ name ] = ( tmp.get( 'success', False ), tmp[ 'results' ], None )

    if wrk:
      result[ 'doc' ] = wrk

    if not result:
      return None

    else:
      return result

  def setResults( self, target, name, results ):
    if target not in ( 'lint', 'test', 'rpm', 'dpkg', 'respkg', 'resource', 'doc' ):
      return

    if target == 'lint':
      self.lint_results[ name ][ 'results' ] = results

    elif target == 'test':
      self.test_results[ name ][ 'results' ] = results

    elif target == 'doc':
      self.doc_results[ name ][ 'results' ] = results

    else:
      self.build_results[ target ][ name ][ 'results' ] = results

    self.full_clean()
    self.save()

  def getResults( self, target ):
    if target == 'lint':
      return dict( [ ( i, self.lint_results[i].get( 'results', None ) ) for i in self.lint_results ] )

    elif target == 'test':
      return dict( [ ( i, self.test_results[i].get( 'results', None ) ) for i in self.test_results ] )

    elif target == 'doc':
      return dict( [ ( i, self.doc_results[i].get( 'results', None ) ) for i in self.doc_results ] )

    elif target in ( 'rpm', 'dpkg', 'respkg', 'resource' ):
      return dict( [ ( i, self.build_results[ target ][i].get( 'results', None ) ) for i in self.build_results[ target ] ] )

    return {}

  def setScore( self, target, name, score ):
    if target not in ( 'lint', 'test' ):
      return

    if target == 'lint':
      self.lint_results[ name ][ 'score' ] = score

    elif target == 'test':
      self.test_results[ name ][ 'score' ] = score

    self.full_clean()
    self.save()

  def getScore( self, target ):
    if target == 'lint':
      return dict( [ ( i, self.lint_results[i].get( 'score', None ) ) for i in self.lint_results ] )

    elif target == 'test':
      return dict( [ ( i, self.test_results[i].get( 'score', None ) ) for i in self.test_results ] )

    return {}

  def signalComplete( self, target, name, success ):
    if target not in ( 'test', 'rpm', 'dpkg', 'respkg', 'resource', 'doc' ):
      return

    if target == 'test':
      self.lint_results[ name ][ 'status' ] = 'done'
      self.lint_results[ name ][ 'success' ] = success

      self.test_results[ name ][ 'status' ] = 'done'
      self.test_results[ name ][ 'success' ] = success

    elif target == 'doc':
      self.doc_results[ name ][ 'status' ] = 'done'
      self.doc_results[ name ][ 'success' ] = success

    else:
      self.build_results[ target ][ name ][ 'status' ] = 'done'
      self.build_results[ target ][ name ][ 'success' ] = success

    self.full_clean()
    self.save()

  def postInProcess( self ):
    if self.project.type != 'GitHubProject':
      return

    if not self.branch.startswith( '_PR' ):
      return

    gh = self.project.githubproject.github
    gh.postCommitStatus( self.commit, 'pending' )

  def postResults( self ):
    if self.project.type != 'GitHubProject':
      return

    gh = self.project.githubproject.github

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

      if summary[ 'status' ] == 'Success':
        gh.postCommitStatus( self.commit, 'success', description='Passed' )
      elif summary[ 'status' ] == 'Failed':
        gh.postCommitStatus( self.commit, 'failure', description='Failure' )
      else:
        gh.postCommitStatus( self.commit, 'error', description='Bad State "{0}"'.format( summary[ 'status' ] ) )

      # gh.setOwner()

      number = int( self.branch[3:] )
      gh.postPRComment( number, _commitSumary2Str( self.summary ) )

  def tagVersion( self ):
    if self.version is None:
      return

    self.project.internal_git.tag( self.version, _commitSumary2Str( self.summary ) )

  @cinp.list_filter( name='project', paramater_type_list=[ { 'type': 'Model', 'model': Project } ] )
  @staticmethod
  def filter_project( project ):
    return Commit.objects.filter( project=project ).order_by( '-created' )

  @cinp.list_filter( name='in_process', paramater_type_list=[] )
  @staticmethod
  def filter_in_process():
    return Commit.objects.filter( done_at__isnull=True )

  @cinp.check_auth()
  @staticmethod
  def checkAuth( user, verb, id_list, action=None ):
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

  def __str__( self ):
    return 'Commit "{0}" on branch "{1}" of project "{2}"'.format( self.commit, self.branch, self.project.name )


@cinp.model( not_allowed_verb_list=[ 'CREATE', 'DELETE', 'UPDATE', 'CALL' ] )
class PackageFile( models.Model ):  # TODO: move this to Project and tie to the commit instead of the group name
  filename = models.CharField( max_length=PACKAGE_FILENAME_LENGTH )
  package = models.ForeignKey( Package, on_delete=models.CASCADE )
  packrat_id = models.CharField( max_length=100, unique=True )
  commit = models.ForeignKey( Commit, on_delete=models.CASCADE )
  created = models.DateTimeField( editable=False, auto_now_add=True )
  updated = models.DateTimeField( editable=False, auto_now=True )

  @cinp.list_filter( name='project', paramater_type_list=[ { 'type': 'Model', 'model': Package } ] )
  @staticmethod
  def filter_package( package ):
    return PackageFile.objects.filter( package=package ).order_by( '-created' )

  @cinp.list_filter( name='commit', paramater_type_list=[ { 'type': 'Model', 'model': Commit } ] )
  @staticmethod
  def filter_commit( commit ):
    return PackageFile.objects.filter( commit=commit ).order_by( '-created' )

  @cinp.check_auth()
  @staticmethod
  def checkAuth( user, verb, id_list, action=None ):
    return cinp.basic_auth_check( user, verb, PackageFile )

  class Meta:
    default_permissions = ()

  def __str__( self ):
    return 'PackageFile "{0}" of "{1}"'.format( self.packrat_id, self.package )


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
    return Build.objects.filter( project=project )

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

    for name in self.network_map.keys():
      if not name_regex.match( name ):
        errors[ 'network_map' ] = 'Invalid network name "{0}"'.format( name )

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
  tag = models.CharField( max_length=TAG_NAME_LENGTH )

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
    return 'BuildDependancies from "{0}" to "{1}" tag "{2}"'.format( self.build.name, self.package.name, self.tag )

  class Meta:
    unique_together = ( 'build', 'package' )


@cinp.model( not_allowed_verb_list=[ 'CREATE', 'DELETE', 'UPDATE', 'CALL' ] )
class BuildResource( models.Model ):
  key = models.CharField( max_length=250, editable=False, primary_key=True )  # until django supports multi filed primary keys
  build = models.ForeignKey( Build, on_delete=models.CASCADE )
  name = models.CharField( max_length=50 )
  resource = models.ForeignKey( Resource, on_delete=models.PROTECT )
  blueprint = models.CharField( max_length=BLUEPRINT_NAME_LENGTH )
  config_values = MapField( blank=True )
  quantity = models.IntegerField( default=1 )
  autorun = models.BooleanField( default=False )
  interface_map = MapField( blank=True )

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
