from django.conf import settings

from cinp.server_werkzeug import WerkzeugServer
from cinp.server_common import Model, Action, Paramater

from mcp.User.models import getUser


class BlankTransaction():
  def commit( self ):
    pass

  def abort( self ):
    pass


def contractorInfo():
  return { 'host': settings.CONTRACTOR_HOST }


def get_app( debug ):
  app = WerkzeugServer( root_path='/api/v1/', root_version='0.9', debug=debug, get_user=getUser, cors_allow_list=[ '*' ] )

  config = Model( name='config', field_list=[], transaction_class=BlankTransaction )
  config.checkAuth = lambda user, verb, id_list: True
  app.root_namespace.addElement( config )

  info = Action( name='getContractorInfo', return_paramater=Paramater( type='Map' ), func=contractorInfo )
  info.checkAuth = lambda user, verb, id_list: True
  config.addAction( info )

  app.registerNamespace( '/', 'mcp.User' )
  app.registerNamespace( '/', 'mcp.Resource' )
  app.registerNamespace( '/', 'mcp.Project' )
  app.registerNamespace( '/', 'mcp.Processor' )

  app.validate()

  return app
