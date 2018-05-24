import logging
from cinp import client

PACKRAT_API_VERSION = 'v1.1'


class Packrat():
  def __init__( self, host, proxy, name, psk ):
    self.name = name
    self.cinp = client.CInP( host, '/api/v1', proxy )
    root = self.cinp.describe( '/api/v1/Repos' )[0]
    if root[ 'api-version' ] != PACKRAT_API_VERSION:
      raise Exception( 'Expected API version "{0}" found "{1}"'.format( PACKRAT_API_VERSION, root[ 'api-version' ] ) )
    logging.debug( 'packrat: login' )
    self.token = self.cinp.call( '/api/v1/Auth(login)', { 'username': self.name, 'password': psk } )[ 'value' ]
    self.cinp.setAuth( name, self.token )

  def logout( self ):
    logging.debug( 'packrat: logout' )
    self.cinp.call( '/api/v1/Auth(logout)', { 'token': self.token } )

  def packages( self ):
    logging.debug( 'packrat: listing packages' )
    results = []

    for item in self.cinp.list( '/api/v1/Repos/Package', count=50 )[0]:
      results.append( item.split( ':' )[1] )

    return results

  def package_files( self, package ):
    logging.debug( 'packrat: listing package files for "{0}"'.format( package ) )

    return self.cinp.getObjects( list_args={ 'uri': '/api/v1/Repos/PackageFile', 'filter': 'package', 'values': { 'package': '/api/v1/Repos/Package:{0}:'.format( package ) } } )

  def release_map( self ):
    logging.debug( 'packrat: get release_map' )
    results = {}

    release_map = self.cinp.getObjects( list_args={ 'uri': '/api/v1/Repos/ReleaseType' } )
    for uri in release_map:
      results[ uri ] = release_map[ uri ][ 'name' ]

    return results

  def promote( self, package_file_id, state ):
    logging.debug( 'packrat: promoting package file "{0}" to "{1}"'.format( package_file_id, state ) )
    return self.cinp.call( '{0}(promote)'.format( package_file_id ), { 'to': state } )
