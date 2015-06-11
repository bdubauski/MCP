from django.utils import simplejson

from django.db import models
from django.core.exceptions import ValidationError

from mcp.Projects.models import Build

class QueueItem( models.Model ):
  """
QueueItem
  """
  build = models.ForeignKey( Build )
  priority = models.IntegerField( default=50 ) # higher the value, higer the priority
  manual = models.BooleanField() # if False, will not auto clean up, and will not block the project from updating/re-scaning for new jobs
  resource_status = models.TextField( default='{}' )
  created = models.DateTimeField( editable=False, auto_now_add=True )
  updated = models.DateTimeField( editable=False, auto_now=True )

  def checkResources( self ):
    result = {}
    resource_map = self.build.resources
    for name in resource_map:
      resource = resource_map[ name ][0].native
      quanitity = resource_map[ name ][1]
      tmp = resource.available( quanitity )
      if not tmp:
        result[ resource.name ] = 'Not Available'

    return result

  def allocateResources( self, job ): # warning, dosen't check first, make sure you are sure there are resources aviable before calling
    result = {}
    resource_map = self.build.resources
    for name in resource_map:
      resource = resource_map[ name ][0].native
      quanitity = resource_map[ name ][1]
      config_list = resource.allocate( job, name, quanitity )
      result[ name ] = []
      for config in config_list:
        result[ name ].append( { 'status': 'Allocated', 'config': config } )

    return result

  def save( self, *args, **kwargs ):
    try:
      simplejson.loads( self.resource_status )
    except ValueError:
      raise ValidationError( 'resource_status must be valid JSON' )

    super( QueueItem, self ).save( *args, **kwargs )

  def __unicode__( self ):
    return 'QueueItem for "%s" of priority "%s"' % ( self.build.name, self.priority )


class BuildJob( models.Model ):
  """
BuildJob
  """
  build = models.ForeignKey( Build )
  _resources = models.TextField( default='{}' )
  built_at = models.DateTimeField( editable=False, blank=True, null=True )
  ran_at = models.DateTimeField( editable=False, blank=True, null=True )
  reported_at = models.DateTimeField( editable=False, blank=True, null=True )
  released_at = models.DateTimeField( editable=False, blank=True, null=True )
  manual = models.BooleanField()
  created = models.DateTimeField( editable=False, auto_now_add=True )
  updated = models.DateTimeField( editable=False, auto_now=True )

  @property
  def resources( self ):
    return simplejson.loads( self._resources )

  @property
  def state( self ):
    if self.released_at and self.reported_at and self.ran_at and self.built_at:
      return 'released'

    if self.reported_at and self.ran_at and self.built_at:
      return 'reported'

    if self.ran_at and self.built_at:
      return 'ran'

    if self.built_at:
      return 'built'

    return 'new'

  def updateResourceState( self, name, index, status ):
    tmp = simplejson.loads( self._resources )
    try:
      tmp[ name ][ index ][ 'status' ] = status
    except ( IndexError, KeyError ):
      return
    self._resources = simplejson.dumps( tmp )
    self.save()

  def setResourceSuccess( self, name, index, success ):
    tmp = simplejson.loads( self._resources )
    try:
      tmp[ name ][ index ][ 'success' ] = bool( success )
    except ( IndexError, KeyError ):
      return
    self._resources = simplejson.dumps( tmp )
    self.save()

  def setResourceResults( self, name, index, results ):
    tmp = simplejson.loads( self._resources )
    try:
      tmp[ name ][ index ][ 'results' ] = results
    except ( IndexError, KeyError ):
      return
    self._resources = simplejson.dumps( tmp )
    self.save()

  def save( self, *args, **kwargs ):
    try:
      simplejson.loads( self._resources )
    except ValueError:
      raise ValidationError( 'status must be valid JSON' )

    super( BuildJob, self ).save( *args, **kwargs )

  def __unicode__( self ):
    return 'BuildJob "%s" for build "%s"' % ( self.pk, self.build.name )

  class API:
    not_allowed_methods = ( 'CREATE', 'DELETE', 'UPDATE' )
    actions = {
                 'updateResourceState': [ { 'type': 'String' }, { 'type': 'Integer' }, { 'type': 'String' } ],
                 'setResourceSuccess': [ { 'type': 'String' }, { 'type': 'Integer' }, { 'type': 'Boolean' } ],
                 'setResourceResults': [ { 'type': 'String' }, { 'type': 'Integer' }, { 'type': 'String' } ]
              }
