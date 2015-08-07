import logging
from cinp import client

class Packrat( object ):
  def __init__( self, host, proxy, name, psk ):
    self.name = name
    self.cinp = client.CInP( host, '/api/v1', proxy )
    logging.debug( 'packrat: login' )
    self.token = self.cinp.call( '/api/v1/Auth(login)', { 'username': self.name, 'password': psk } )[ 'value' ]
    self.cinp.setAuth( name, self.token )

  def logout( self ):
    logging.debug( 'packrat: logout' )
    self.cinp.call( '/api/v1/Auth(logout)', { 'username': self.name, 'token': self.token } )

  def packages( self ):
    logging.debug( 'packrat: listing packages' )
    results = []

    for item in self.cinp.list( '/api/v1/Repos/Package', count=50 )[0]:
      results.append( item.split( ':' )[1] )

    return results

  def package_files( self, package ):
    logging.debug( 'packrat: listing package files for "%s"' % package )

    return self.cinp.getObjects( list_args={ 'uri': '/api/v1/Repos/PackageFile', 'filter': 'package', 'values': { 'package': '/api/v1/Repos/Package:%s:' % package } } )

  def promote( self, package_file_id, state ):
    logging.debug( 'packrat: promoting package file "%s" to "%s"' % ( package_file_id, state ) )
    return self.cinp.call( '%s(promote)' % package_file_id, { 'to': state } )
