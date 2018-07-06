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

  def createInstance( self, site_id, complex_id, blueprint_id, hostname, config_values, addressblock_id ):
    foundation = self.cinp.call( '/api/v1/Building/Complex:{0}:(createFoundation)'.format( complex_id ), { 'hostname': hostname, 'can_auto_locate': True } )

    data = {}
    data[ 'site' ] = '/api/v1/Site/Site:{0}:'.format( site_id )
    data[ 'foundation' ] = '/api/v1/Building/Foundation:{0}:'.format( self.cinp.uri.extractIds( foundation )[0] )
    data[ 'hostname' ] = hostname
    data[ 'blueprint' ] = '/api/v1/BluePrint/StructureBluePrint:{0}:'.format( blueprint_id )
    data[ 'config_values' ] = config_values
    data[ 'auto_build' ] = True  # Static stuff builds when it can
    structure = self.cinp.create( '/api/v1/Building/Structure', data )[0]

    data = {}
    data[ 'structure' ] = structure
    data[ 'interface_name' ] = 'eth0'
    data[ 'is_primary' ] = True
    address = self.cinp.call( '/api/v1/Utilities/AddressBlock:{0}:(nextAddress)'.format( addressblock_id ), data )

    logging.debug( 'Created "{0}" on "{1}" at {2}'.format( structure, foundation, address ) )

    self.registerWebHook( )

    return ( self.cinp.uri.extractIds( foundation )[0], self.cinp.uri.extractIds( structure )[0] )

  def destroyInstance( self, foundation_id, structure_id ):
    raise Exception( 'not yet' )

  def destroyFoundation( self, id ):
    self.cinp.call( '/api/v1/Building/Foundation:{0}:(doDestroy)'.format( id ), {} )

  def destroyStructure( self, id ):
    self.cinp.call( '/api/v1/Building/Structure:{0}:(doDestroy)'.format( id ), {} )

  def updateConfig( self, instance_id, config_values, hostname ):
    data = {}
    data[ 'config_values' ] = config_values
    data[ 'hostname' ] = hostname
    self.cinp.update( '/api/v1/Building/Structure:{0}:'.format( instance_id ), data )

    logging.debug( 'Updated config of Structure "{0}" to "{1}"'.format( instance_id, config_values ) )

  def registerWebHook( self, instance, on_build ):
    data = {}
    data[ 'foundation' ] = '/api/v1/Building/Foundation:{9}:'.format( instance.foundation_id )
    data[ 'one_shot' ] = True
    data[ 'extra_data' ] = { 'cookie': instance.cookie }
    data[ 'type' ] = 'call'
    if on_build:
      data[ 'url' ] = '{0}api/v1/Builder/Instance:{1}:(foundationBuild)'.format( settings.MCP_HOST, instance.pk )
    else:
      data[ 'url' ] = '{0}api/v1/Builder/Instance:{1}:(foundationDestroyed)'.format( settings.MCP_HOST, instance.pk )
    self.cinp.create( '/api/v1/PostOffice/FoundationBox', data )

    data = {}
    data[ 'structure' ] = '/api/v1/Building/Structure:{0}:'.format( instance.structure_id )
    data[ 'one_shot' ] = True
    data[ 'extra_data' ] = { 'cookie': instance.cookie }
    data[ 'type' ] = 'call'
    if on_build:
      data[ 'url' ] = '{0}api/v1/Builder/Instance:{1}:(structureBuild)'.format( settings.MCP_HOST, instance.pk )
    else:
      data[ 'url' ] = '{0}api/v1/Builder/Instance:{1}:(structureDestroyed)'.format( settings.MCP_HOST, instance.pk )
    self.cinp.create( '/api/v1/PostOffice/StructureBox', data )
