from cinp.server_werkzeug import WerkzeugServer

from mcp.User.models import getUser


def get_app( debug ):
  app = WerkzeugServer( root_path='/api/v1/', root_version='0.9', debug=debug, get_user=getUser, cors_allow_list=[ '*' ] )

  app.registerNamespace( '/', 'mcp.User' )
  app.registerNamespace( '/', 'mcp.Resource' )
  app.registerNamespace( '/', 'mcp.Project' )
  app.registerNamespace( '/', 'mcp.Processor' )

  app.validate()

  return app
