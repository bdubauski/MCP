from django.conf import settings

from cinp.server_werkzeug import WerkzeugServer
from cinp.server_common import Model, Action, Paramater

from mcp.Auth.models import getUser


class BlankTransaction():
  def __init__( self ):
    super().__init__()

  def get( self, model, object_id ):
    return None

  def create( self, model, value_map ):
    pass

  def update( self, model, object_id, value_map ):
    return None

  def list( self, model, filter_name, filter_values, position, count ):
    return []

  def delete( self, model, object_id ):
    return False

  def start( self ):
    pass

  def commit( self ):
    pass

  def abort( self ):
    pass


def contractorInfo():
  return { 'host': settings.CONTRACTOR_HOST }


def get_app( debug ):
  app = WerkzeugServer( root_path='/api/v1/', root_version='0.10', debug=debug, get_user=getUser, cors_allow_list=[ '*' ] )

  config = Model( name='config', field_list=[], transaction_class=BlankTransaction )
  config.checkAuth = lambda user, verb, id_list: True
  app.root_namespace.addElement( config )

  info = Action( name='getContractorInfo', return_paramater=Paramater( type='Map' ), func=contractorInfo )
  info.checkAuth = lambda user, verb, id_list: True
  config.addAction( info )

  app.registerNamespace( '/', 'mcp.Auth' )
  app.registerNamespace( '/', 'mcp.Resource' )
  app.registerNamespace( '/', 'mcp.Project' )
  app.registerNamespace( '/', 'mcp.Processor' )

  app.validate()

  return app
