import logging

from django.conf import settings

from cinp import client

CONTRACTOR_API_VERSION = '0.9'


def getContractor():
  return Contractor( settings.CONTRACTOR_HOST, settings.CONTRACTOR_PROXY, settings.CONTRACTOR_USERNAME, settings.CONTRACTOR_PSK )


class Contractor():
  def __init__( self, host, proxy, username, password ):
    super().__init__()
    self.username = username
    logging.debug( 'contractor: connecting...' )
    self.cinp = client.CInP( host, '/api/v1/', proxy )

    root = self.cinp.describe( '/api/v1/' )
    if root[ 'api-version' ] != CONTRACTOR_API_VERSION:
      raise Exception( 'Expected API version "{0}" found "{1}"'.format( CONTRACTOR_API_VERSION, root[ 'api-version' ] ) )

    logging.debug( 'packrat: login' )
    self.token = self.cinp.call( '/api/v1/Auth/User(login)', { 'username': self.username, 'password': password } )
    self.cinp.setAuth( username, self.token )

  def logout( self ):
    logging.debug( 'packrat: logout' )
    self.cinp.call( '/api/v1/Auth/User(logout)', { 'token': self.token } )

  def getNetworkInfo( self, id ):
    block = self.cinp.get( '/api/v1/Utilities/AddressBlock:{0}'.format( id ) )

    return block

  def getNetworkUsage( self, id ):
    usage = self.cinp.call( '/api/v1/Utilities/AddressBlock:{0}:(usage)'.format( id ), {} )

    return usage

  def getStructures( self, id_list ):
    return self.cinp.getObjets( '/api/v1/Building/Structure', id_list ).values()

  def createInstance( self, site_id, complex_id, blueprint_id, hostname, config_values, interface_map ):
    foundation = self.cinp.call( '/api/v1/Building/Complex:{0}:(createFoundation)'.format( complex_id ), { 'hostname': hostname, 'interface_name_list': [] } )

    data = {}
    data[ 'site' ] = '/api/v1/Site/Site:{0}:'.format( site_id )
    data[ 'foundation' ] = '/api/v1/Building/Foundation:{0}:'.format( self.cinp.uri.extractIds( foundation )[0] )
    data[ 'hostname' ] = hostname
    data[ 'blueprint' ] = '/api/v1/BluePrint/StructureBluePrint:{0}:'.format( blueprint_id )
    data[ 'config_values' ] = config_values
    structure = self.cinp.create( '/api/v1/Building/Structure', data )[0]

    counter = 0
    for name, interface in interface_map.items():
      data = {}
      data[ 'foundation' ] = foundation
      data[ 'name' ] = name
      data[ 'physical_location' ] = 'eth{0}'.format( counter )
      data[ 'is_provisioning' ] = bool( counter == 0 )
      self.cinp.create( '/api/v1/Utilities/RealNetworkInterface', data )
      counter += 1

      data = {}
      data[ 'networked' ] = structure.replace( '/Building/Structure:', '/Utilities/Networked:' )
      data[ 'interface_name' ] = name
      data[ 'is_primary' ] = interface[ 'is_primary' ]

      offset = interface.get( 'offset', None )

      if offset is not None:
        data[ 'offset' ] = offset
        data[ 'address_block' ] = '/api/v1/Utilities/AddressBlock:{0}:'.format( interface[ 'network' ] )
        address = self.cinp.create( '/api/v1/Utilities/Address', data )
      else:
        address = self.cinp.call( '/api/v1/Utilities/AddressBlock:{0}:(nextAddress)'.format( interface[ 'network' ] ), data )

    logging.debug( 'Created "{0}" on "{1}" at {2}'.format( structure, foundation, address ) )

    return ( self.cinp.uri.extractIds( foundation )[0], self.cinp.uri.extractIds( structure )[0] )

  def createFoundation( self, id ):
    self.cinp.call( '/api/v1/Building/Foundation:{0}:(setLocated)'.format( id ), {} )
    self.cinp.call( '/api/v1/Building/Foundation:{0}:(doCreate)'.format( id ), {} )

  def createStructure( self, id ):
    self.cinp.call( '/api/v1/Building/Structure:{0}:(doCreate)'.format( id ), {} )

  def destroyFoundation( self, id ):
    self.cinp.call( '/api/v1/Building/Foundation:{0}:(doDestroy)'.format( id ), {} )

  def destroyStructure( self, id ):
    self.cinp.call( '/api/v1/Building/Structure:{0}:(doDestroy)'.format( id ), {} )

  def deleteFoundation( self, id ):
    self.cinp.delete( '/api/v1/Building/Foundation:{0}:'.format( id ) )

  def deleteStructure( self, id ):
    self.cinp.delete( '/api/v1/Building/Structure:{0}:'.format( id ) )

  def updateConfig( self, instance_id, config_values, hostname ):
    data = {}
    data[ 'config_values' ] = config_values
    data[ 'hostname' ] = hostname
    self.cinp.update( '/api/v1/Building/Structure:{0}:'.format( instance_id ), data )

    logging.debug( 'Updated config of Structure "{0}" to "{1}"'.format( instance_id, config_values ) )

  def registerWebHook( self, instance, on_build ):
    data = {}
    data[ 'one_shot' ] = True
    data[ 'extra_data' ] = { 'cookie': instance.cookie }
    data[ 'type' ] = 'call'
    if on_build:
      data[ 'structure' ] = '/api/v1/Building/Structure:{0}:'.format( instance.structure_id )
      data[ 'url' ] = '{0}/api/v1/Processor/Instance:{1}:(isBuilt)'.format( settings.MCP_HOST, instance.pk )
      self.cinp.create( '/api/v1/PostOffice/StructureBox', data )

    else:
      data[ 'foundation' ] = '/api/v1/Building/Foundation:{0}:'.format( instance.foundation_id )
      data[ 'url' ] = '{0}/api/v1/Processor/Instance:{1}:(isDestroyed)'.format( settings.MCP_HOST, instance.pk )
      self.cinp.create( '/api/v1/PostOffice/FoundationBox', data )
