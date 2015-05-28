from django.utils import simplejson

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

class Package( models.Model ):
  """
This is a Package
  """
  name = models.CharField( max_length=100, primary_key=True )
  cur_state = models.CharField( max_length=RELEASE_TYPE_LENGTH, choices=RELEASE_TYPE_CHOICES )
  created = models.DateTimeField( editable=False, auto_now_add=True )
  updated = models.DateTimeField( editable=False, auto_now=True )

  def __unicode__( self ):
    return "Package '%s'" % self.name


class Build( models.Model ):
  """
This is a type of Build that can be done
  """
  name = models.CharField( max_length=100 )
  project = models.ForeignKey( Project )
  _dependancies = models.ManyToManyField( Package )
  _states = models.CharField( max_length=255 )
  _resources = models.ManyToManyField( Resource )
  _quanities = models.CharField( max_lgnth=255 )
  created = models.DateTimeField( editable=False, auto_now_add=True )
  updated = models.DateTimeField( editable=False, auto_now=True )

  @property
  def dependancies( self ):
    tmp = self._states.split( ',' )
    return zip( self._dependancies, tmp )

  @property
  def reqources( self ):
    tmp = [ int( i ) for i in self._quanities.split( ',' ) ]
    return zip( self._resources, tmp )

  def save( self, *args, **kwargs ):
    try:
      simplejson.loads( self.resources )
    except ValueError:
      raise ValidationError( 'resources must be valid JSON' )

    super( Build, self ).save( *args, **kwargs )

  def __unicode__( self ):
    return "Build '%s' of '%s'" % ( self.name, self.project.name )
