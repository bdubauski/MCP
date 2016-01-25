import re

from django.utils import simplejson
from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings

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
  def busy( self ): # ie. can it be updated, and scaned for new things to do
    not_busy = True
    for build in self.build_set.all():
      for item in build.queueitem_set.all():
        not_busy &= item.manual

      for job in build.buildjob_set.all():
        not_busy &= item.manual

    return not not_busy

  @property
  def git_url( self ):
    return '%s%s' % ( settings.GIT_HOST, self.local_path )

  def save( self, *args, **kwargs ):
    if not re.match( '^[a-z0-9][a-z0-9\-]*[a-z0-9]$', self.name ):
      raise ValidationError( 'Invalid name' )

    if not self.local_path:
      self.local_path = None

    super( Project, self ).save( *args, **kwargs )

  def __unicode__( self ):
    return 'Project "%s"' % self.name


class GitHubProject( Project ):
  """
This is a GitHub Project
  """
  github_url = models.CharField( max_length=200 )

  def __unicode__( self ):
    return 'GitHub Project "%s"' % self.name


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


class Commit( models.Model ):
  """
A Single Commit of a Project
  """
  project = models.ForeignKey( Project )
  branch = models.CharField( max_length=50 )
  commit = models.CharField( max_length=45 )
  lint_results = models.TextField( default='{}' )
  test_results = models.TextField( default='{}' )
  build_results = models.TextField( default='{}')
  lint_at = models.DateTimeField( editable=False, blank=True, null=True )
  test_at = models.DateTimeField( editable=False, blank=True, null=True )
  build_at = models.DateTimeField( editable=False, blank=True, null=True )
  done_at = models.DateTimeField( editable=False, blank=True, null=True )
  created = models.DateTimeField( editable=False, auto_now_add=True )
  updated = models.DateTimeField( editable=False, auto_now=True )

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
    results = resources[ 'target' ][0].get( 'results', '<not specified>' )

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

  def __unicode__( self ):
    return 'Commit "%s" on branch "%s" of project "%s"' % ( self.commit, self.branch, self.project.name )

  class Meta:
      unique_together = ( 'project', 'commit' )

class Build( models.Model ):
  """
This is a type of Build that can be done
  """
  key = models.CharField( max_length=160, editable=False, primary_key=True ) # until djanog supports multi filed primary keys
  name = models.CharField( max_length=100 )
  project = models.ForeignKey( Project )
  dependancies = models.ManyToManyField( Package, through='BuildDependancy' )
  resources = models.ManyToManyField( Resource, through='BuildResource' )
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

    self.key = '%s:%s' % ( self.project.name, self.name )

    super( Build, self ).save( *args, **kwargs )

  def __unicode__( self ):
    return 'Build "%s" of "%s"' % ( self.name, self.project.name )

  class Meta:
      unique_together = ( 'name', 'project' )

class BuildDependancy( models.Model ):
  key = models.CharField( max_length=250, editable=False, primary_key=True ) # until django supports multi filed primary keys
  build = models.ForeignKey( Build )
  package = models.ForeignKey( Package )
  state = models.CharField( max_length=RELEASE_TYPE_LENGTH, choices=RELEASE_TYPE_CHOICES )

  def save( self, *args, **kwargs ):
    self.key = '%s:%s' % ( self.build.key, self.package.name )

    super( BuildDependancy, self ).save( *args, **kwargs )

  def __unicode__( self ):
    return 'BuildDependancies from "%s" to "%s" at "%s"' % ( self.build.name, self.package.name, self.state )

  class Meta:
      unique_together = ( 'build', 'package' )

class BuildResource( models.Model ):
  key = models.CharField( max_length=250, editable=False, primary_key=True ) # until djanog supports multi filed primary keys
  build = models.ForeignKey( Build )
  resource = models.ForeignKey( Resource )
  name = models.CharField( max_length=50 )
  quanity = models.IntegerField( default=1 )

  def save( self, *args, **kwargs ):
    self.key = '%s:%s:%s' % ( self.build.key, self.name, self.resource.name )

    super( BuildResource, self ).save( *args, **kwargs )

  def __unicode__( self ):
    return 'BuildResource from "%s" for "%s" named "%s"' % ( self.build.name, self.resource.name, self.name )

  class Meta:
      unique_together = ( 'build', 'name' )
