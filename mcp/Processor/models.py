from django.utils import simplejson

from django.db import models
from django.core.exceptions import ValidationError

from mcp.Projects.models import Build

class QueueItem( models.Model ):
  """
Processing Queue
  """
  build = models.ForeignKey( Build )
  priority = models.IntegerField( devault=50 ) # higher the value, higer the priority
  manual = models.BooleanField() # ie. does it auto cleanup
  resource_status = models.TextField()
  created = models.DateTimeField( editable=False, auto_now_add=True )
  updated = models.DateTimeField( editable=False, auto_now=True )

  def getResources( self ):
    resources = self.build.resources

    print resources

    return [ 1, 2, 3 ]

  def __unicode__( self ):
    return "QueueItem for '%s' of priority '%s'" % ( self.build.name, self.priority )


class BuildJob( models.Model ):
  """
BuildJob
  """
  build = models.ForeignKey( Build )
  _resources = models.CharField( max_length=200 )
  status = models.TextField( default='{}' )
  created = models.DateTimeField( editable=False, auto_now_add=True )
  updated = models.DateTimeField( editable=False, auto_now=True )

  @property
  def resources( self ):
    return [ int( i ) for i in self._resources.split( ',' ) ]

  @resources.setter
  def resources( self, value ):
    for i in value:
      if not isinstance( i, int ):
        raise ValidationError( 'Resources Must be a an Itertable of ints. Got "%s"' % value )

    self._resources = ','.join( value )

  def setStatus( self, resource, status ):
    status = simplejson.loads( self.status )
    status[ resource ] = status
    self.status = simplejson.dumps( status )
    self.save()

  def save( self, *args, **kwargs ):
    try:
      simplejson.loads( self.status )
    except ValueError:
      raise ValidationError( 'status must be valid JSON' )

    super( BuildJob, self ).save( *args, **kwargs )

  def __unicode__( self ):
    return "BuildJob '%s' for build '%s'" % ( self.pk, self.build.name )
