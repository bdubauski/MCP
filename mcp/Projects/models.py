import re

from django.db import models
from django.core.exceptions import ValidationError

from mcp.Resources.models import Resource

# from packrat Repos/models.py
RELEASE_TYPE_LENGTH = 5
RELEASE_TYPE_CHOICES = ( ( 'ci', 'CI' ), ( 'dev', 'Development' ), ( 'stage', 'Staging' ), ( 'prod', 'Production' ), ( 'depr', 'Deprocated' ) )


class Project( models.Model ):
  """
This is a Generic Project
  """
  name = models.CharField( max_length=50, primary_key=True )
  local_path = models.CharField( max_length=50, editable=False )
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

  def save( self, *args, **kwargs ):
    if not re.match( '^[a-z0-9][a-z0-9\-]*[a-z0-9]$', self.name ):
      raise ValidationError( 'Invalid name' )

    super( Project, self ).save( *args, **kwargs )

  def __unicode__( self ):
    return "Project '%s'" % self.name


class GitHubProject( Project ):
  """
This is a GitHub Project
  """
  github_url = models.CharField( max_length=200 )
  last_commit = models.CharField( max_length=45 )

  def __unicode__( self ):
    return "GitHub Project '%s'" % self.name

  def setup( self ):
    pass
    # git --bare clone %uri
    # git --bare update-server-info
    # mv hooks/post-update.sample hooks/post-update

  def refresh( self ):
    pass
    # git fetch


class Package( models.Model ):
  """
This is a Package
  """
  name = models.CharField( max_length=100, primary_key=True )
  cur_state = models.CharField( max_length=RELEASE_TYPE_LENGTH, choices=RELEASE_TYPE_CHOICES )
  created = models.DateTimeField( editable=False, auto_now_add=True )
  updated = models.DateTimeField( editable=False, auto_now=True )

  def save( self, *args, **kwargs ):
    if not re.match( '^[a-z0-9][a-z0-9\-]*[a-z0-9]$', self.name ):
      raise ValidationError( 'Invalid name' )

    super( Package, self ).save( *args, **kwargs )

  def __unicode__( self ):
    return 'Package "%s"' % self.name


class Build( models.Model ):
  """
This is a type of Build that can be done
  """
  name = models.CharField( max_length=100, primary_key=True )
  project = models.ForeignKey( Project )
  _dependancies = models.ManyToManyField( Package, through='BuildDependancy' )
  _resources = models.ManyToManyField( Resource, through='BuildResource' )
  manual = models.BooleanField()
  created = models.DateTimeField( editable=False, auto_now_add=True )
  updated = models.DateTimeField( editable=False, auto_now=True )

  @property
  def dependancies( self ):
    result = {}
    for dependancy in self.builddependancy_set.all():
      result[ dependancy.dependancy ] = dependancy.state

    return result

  @dependancies.setter
  def dependancies( self, value ):
    self.builddependancy_set.clear()
    for dependancy in value:
      tmp = BuildDependancy()
      tmp.build = self
      tmp.dependancy = dependancy
      tmp.state = value[ dependancy ]
      tmp.save()

  @property
  def resources( self ):
    result = {}
    for resource in self.buildresource_set.all():
      result[ resource.name ] = ( resource.resource, resource.quanity )

    return result

  @resources.setter
  def resources( self, value ):
    self.buildresource_set.clear()
    for name in value:
      resource = value[ name ]
      if isinstance( resource, tuple ):
        ( resource, quanity ) = value

      else:
        quanity = 1

      tmp = BuildResource()
      tmp.build = self
      tmp.resource = resource
      tmp.name = name
      tmp.quanity = quanity
      tmp.save()

  def save( self, *args, **kwargs ):
    if not re.match( '^[a-z0-9][a-z0-9\-]*[a-z0-9]$', self.name ):
      raise ValidationError( 'Invalid name' )

    super( Build, self ).save( *args, **kwargs )

  def __unicode__( self ):
    return 'Build "%s" of "%s"' % ( self.name, self.project.name )

class BuildDependancy( models.Model ):
  key = models.CharField( max_length=200, editable=False, primary_key=True ) # until djanog supports multi filed primary keys
  build = models.ForeignKey( Build )
  dependancy = models.ForeignKey( Package )
  state = models.CharField( max_length=RELEASE_TYPE_LENGTH, choices=RELEASE_TYPE_CHOICES )

  def save( self, *args, **kwargs ):
    self.key = '%s:%s' % ( self.build.name, self.dependancy.name )

    super( BuildDependancy, self ).save( *args, **kwargs )

  def __unicode__( self ):
    return 'BuildDependancies from "%s" to "%s" at "%s"' % ( self.build.name, self.dependancy.name, self.state )

  class Meta:
      unique_together = ( 'build', 'dependancy' )

class BuildResource( models.Model ):
  key = models.CharField( max_length=200, editable=False, primary_key=True ) # until djanog supports multi filed primary keys
  build = models.ForeignKey( Build )
  resource = models.ForeignKey( Resource )
  name = models.CharField( max_length=50 )
  quanity = models.IntegerField( default=1 )

  def save( self, *args, **kwargs ):
    self.key = '%s:%s' % ( self.build.name, self.resource.name )

    super( BuildResource, self ).save( *args, **kwargs )

  def __unicode__( self ):
    return 'BuildResource from "%s" for "%s" named "%s"' % ( self.build.name, self.resource.name, self.name )

  class Meta:
      unique_together = ( 'build', 'name' )
