import logging
from cinp import client

PACKRAT_API_VERSION = '2.0'


class Packrat():
  def __init__( self, host, proxy, name, psk ):
    self.name = name
    self.cinp = client.CInP( host, '/api/v2/', proxy )

    root = self.cinp.describe( '/api/v2/' )
    if root[ 'api-version' ] != PACKRAT_API_VERSION:
      raise Exception( 'Expected API version "{0}" found "{1}"'.format( PACKRAT_API_VERSION, root[ 'api-version' ] ) )

    logging.debug( 'packrat: login' )
    self.token = self.cinp.call( '/api/v2/Auth/User(login)', { 'username': self.name, 'password': psk } )
    self.cinp.setAuth( name, self.token )

  def logout( self ):
    logging.debug( 'packrat: logout' )
    self.cinp.call( '/api/v2/Auth/User(logout)', { 'token': self.token } )

  def packages( self ):
    logging.debug( 'packrat: listing packages' )
    results = []

    for item in self.cinp.list( '/api/v2/Package/Package', count=50 )[0]:
      results.append( item.split( ':' )[1] )

    return results

  def package_files( self, package ):
    logging.debug( 'packrat: listing package files for "{0}"'.format( package ) )

    return self.cinp.getFilteredObjects( '/api/v2/Package/PackageFile', 'package', { 'package': '/api/v2/Package/Package:{0}:'.format( package ) } )

  def tag_map( self ):
    logging.debug( 'packrat: get tag_map' )
    results = {}

    tag_map = self.cinp.call( '/api/v2/Attrib/Tag(tagMap)', {} )
    for ( uri, release ) in tag_map:
      results[ uri ] = release[ 'name' ]

    return results

  def tag( self, package_file_id, tag ):
    logging.debug( 'packrat: tagging package file "{0}" with "{1}"'.format( package_file_id, tag ) )
    return self.cinp.call( '{0}(tag)'.format( package_file_id ), { 'tag': '/api/v2/Attrib/Tag:{0}:'.format( tag ) } )
