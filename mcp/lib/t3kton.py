import logging

from django.conf import settings

from cinp import client

CONTRACTOR_API_VERSION = '0.9'


def getContractor():
  return Contractor( settings.CONTRACTOR_HOST, settings.CONTRACTOR_PROXY )


class Contractor():
  def __init__( self, host, proxy=None ):
    super().__init__()
    logging.debug( 'contractor: connecting...' )
    self.cinp = client.CInP( host, '/api/v1/', proxy )
    root = self.cinp.describe( '/api/v1/' )
    if root[ 'api-version' ] != CONTRACTOR_API_VERSION:
      raise Exception( 'Expected API version "{0}" found "{1}"'.format( CONTRACTOR_API_VERSION, root[ 'api-version' ] ) )

  def getNetworkInfo( self, name ):
    block = self.cinp.get( '/api/v1/Utilities/AddressBlock:{0}'.format( name ) )

    return block

  def getNetworkUsage( self, name ):
    usage = self.cinp.call( '/api/v1/Utilities/AddressBlock:{0}:(usage)'.format( name ), {} )

    return usage

  def getStructures( self, id_list ):
    return self.cinp.getObjets( '/api/v1/Building/Structure', id_list ).values()
