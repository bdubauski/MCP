import logging
from cinp import client

from django.conf import settings

PACKRAT_API_VERSION = '2.0'


def getPackrat():
  logging.debug( 'packrat: connecting to Packrat...' )
  return Packrat( settings.PACKRAT_HOST, settings.PACKRAT_PROXY, settings.PACKRAT_USERNAME, settings.PACKRAT_PASSWORD )


class Packrat():
  def __init__( self, host, proxy, username, password ):
    super().__init__()
    self.username = username
    self.cinp = client.CInP( host, '/api/v2/', proxy )

    root = self.cinp.describe( '/api/v2/' )
    if root[ 'api-version' ] != PACKRAT_API_VERSION:
      raise Exception( 'Expected API version "{0}" found "{1}"'.format( PACKRAT_API_VERSION, root[ 'api-version' ] ) )

    logging.debug( 'packrat: login' )
    self.token = self.cinp.call( '/api/v2/Auth/User(login)', { 'username': self.username, 'password': password } )
    self.cinp.setAuth( username, self.token )

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

  def tag_requirements_map( self ):
    logging.debug( 'packrat: get tag_requirements_map' )
    results = {}

    tag_map = self.cinp.call( '/api/v2/Attrib/Tag(tagMap)', {} )
    for ( tag, info ) in tag_map.items():
      if info[ 'change_control' ]:  # we can't promote these anyway
        continue
      results[ tag ] = info[ 'required' ]

    return results

  def tag( self, package_file_id, tag ):
    logging.debug( 'packrat: tagging package file "{0}" with "{1}"'.format( package_file_id, tag ) )
    try:
      self.cinp.call( '{0}(tag)'.format( package_file_id ), { 'tag': '/api/v2/Attrib/Tag:{0}:'.format( tag ) } )
    except client.DetailedInvalidRequest as e:
      if e.error != 'ALLREADY_TAGGED':
        raise e

  def fail( self, package_file_id ):
    logging.debug( 'packrat: failing package file "{0}"'.format( package_file_id ) )
    self.cinp.call( '{0}(fail)'.format( package_file_id ), {} )
