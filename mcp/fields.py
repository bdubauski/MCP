import re
import pickle

from django.db import models
from django.core.exceptions import ValidationError

name_regex = re.compile( '^[a-zA-Z0-9][a-zA-Z0-9_\-]*$' )
package_filename_regex = re.compile( '^[0-9a-zA-Z\-_\.]+$' )  # from packrat.fields.filename_regex
packagefile_regex = re.compile( '/api/v2/Package/PackageFile:[0-9]+:')
TAG_NAME_LENGTH = 10  # from packrat Attrib/models.py, length of the Tag name
PACKAGE_FILENAME_LENGTH = 100  # something some where in packrat defines this?


def defaultdict():
  return dict()


class MapField( models.BinaryField ):
  description = 'Map Field'
  cinp_type = 'Map'
  empty_values = [ None, {} ]

  def __init__( self, *args, **kwargs ):
    if 'default' in kwargs:
      default = kwargs[ 'default' ]
      if kwargs.get( 'null', False ) and default is None:
        pass

      elif not callable( default ) and not isinstance( default, dict ):
        raise ValueError( 'default value must be a dict or callable.' )

    else:
      kwargs[ 'default' ] = defaultdict

    editable = kwargs.get( 'editable', True )
    super().__init__( *args, **kwargs )  # until Django 2.1, editable for BinaryFields is not able to be made editable
    self.editable = editable

  def deconstruct( self ):
    editable = self.editable
    self.editable = False  # have to set this to non default so BinaryField's deconstruct works
    name, path, args, kwargs = super( MapField, self ).deconstruct()
    self.editable = editable
    kwargs[ 'editable' ] = self.editable
    return name, path, args, kwargs

  def from_db_value( self, value, expression, connection, context ):
    if value is None:
      return None

    try:
      value = pickle.loads( value )
    except ValueError:
      raise ValidationError( 'DB Value is not a valid Pickle.', code='invalid' )

    if value is not None and not isinstance( value, dict ):
      raise ValidationError( 'DB Stored Value does not encode a dict.', code='invalid' )

    return value

  def to_python( self, value ):
    if value is None and self.null:
      return None

    if isinstance( value, dict ):
      return value

    raise ValidationError( 'must be a dict.', code='invalid'  )

  def get_prep_value( self, value ):
    if value is None:
      return None

    if not isinstance( value, dict ):
      raise ValidationError( 'value is not a dict.', code='invalid'  )

    return pickle.dumps( value, protocol=4 )
