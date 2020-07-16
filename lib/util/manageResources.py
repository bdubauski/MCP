#!/usr/bin/env python3
import os

os.environ.setdefault( 'DJANGO_SETTINGS_MODULE', 'mcp.settings' )

import django
django.setup()

import sys
import argparse
import cinp
from datetime import datetime, timezone

from mcp.Project.models import Project, Build, BuildResource
from mcp.Resource.models import BluePrint, Site, Network, DynamicResource
from mcp.lib.t3kton import getContractor

RESOURCE_OS_LIST = ( 'ubuntu-trusty', 'ubuntu-xenial', 'ubuntu-bionic', 'debian-buster', 'centos-6', 'centos-7', 'esx', 'proxmox' )

parser = argparse.ArgumentParser( description='resource manager - add/remove static and dynamic resources' )
parser.add_argument( '--dynamic-resource-blueprint', help='blueprint for the resources hosted on the resource complex' )

parser.add_argument( '--blueprint-list', help='List the (Structure) Blueprints', action='store_true' )
parser.add_argument( '--blueprint-add', help='Add a (Structure) Blueprint, this should be the name on Contractor', metavar='BLUEPRINT NAME' )
parser.add_argument( '--blueprint-remove', help='Remove a (Structure) Blueprints, this should be the network id in MCP', metavar='BLUEPRINT NAME' )

parser.add_argument( '--site-list', help='List the Curent Sites', action='store_true'  )
parser.add_argument( '--site-add', help='Add a Site, this should be the site name on Contractor', metavar='SITE NAME' )
parser.add_argument( '--site-remove', help='Remove a Site, this should be the site name in MCP', metavar='SITE NAME' )

parser.add_argument( '--site', help='Site for required operations', metavar='SITE NAME' )

parser.add_argument( '--network-list', help='List the Curent Networks in specified Site', action='store_true' )
parser.add_argument( '--network-add', help='Add a Network, this should be "network id:addressblock id" on Contractor, requires site paramater', metavar='NETWORK NAME' )
parser.add_argument( '--network-remove', help='Remove a Network, this should be the network id in MCP', metavar='NETWORK NAME' )

parser.add_argument( '--dynamic-resource-list', help='List the Curent Dynamic Resources', action='store_true' )
parser.add_argument( '--dynamic-resource-add', help='Add a Dynamic Resource, this should be the complex id on Contractor, requires site paramater', metavar='NETWORK NAME' )
parser.add_argument( '--dynamic-resource-remove', help='Remove a Dynamic Resource, this should be the network id in MCP', metavar='NETWORK NAME' )

# this one is a hack and is temporary until the dynamic/bluprint/stuff mess is figured out
parser.add_argument( '--update-builtin', help='Update the Builtin project with the curent blueprints', action='store_true' )

args = parser.parse_args()

site = None
if args.site:
  try:
    site = Site.objects.get( name=args.site )
  except Site.DoesNotExist:
    print( 'Site "{0}" not found in MCP'.format( args.site ) )
    sys.exit( 1 )

# list operations
if args.blueprint_list:
  print( 'Name      Contractor Name' )
  print( '-------------------------' )
  for blueprint in BluePrint.objects.all().order_by( 'pk' ):
    print( '{0}   {1}'.format( blueprint.name, blueprint.contractor_blueprint_id ) )

  sys.exit( 0 )

if args.site_list:
  print( 'Name' )
  print( '----' )
  for site in Site.objects.all().order_by( 'pk' ):
    print( site.name )

  sys.exit( 0 )

if ( args.network_list or args.dynamic_resource_list ) and site is None:
  print( 'Site Required' )
  sys.exit( 1 )

if args.network_list:
  print( 'Name     Size  Monolythic  Contractor Address Block  Contractor Network' )
  print( '-----------------------------------------------------------------------' )
  for network in Network.objects.filter( site=site ):
    print( '{0}  {1}  {2}  {3}  {4}'.format( network.name, network.site, network.monalythic, network.contractor_addressblock_id, network.contractor_network_id ) )

  sys.exit( 0 )

if args.dynamic_resource_list:
  print( 'Name     Description      Contractor Id' )
  print( '---------------------------------------' )
  for resource in DynamicResource.objects.filter( site=site ):
    print( '{0}  {1}  {2}'.format( resource.name, resource.description, resource.complex_id ) )

  sys.exit( 0 )

contractor = getContractor()

# blueprint operations
if args.blueprint_add:
  try:
    contractor_site = contractor.getBluePrint( args.blueprint_add )
  except cinp.client.NotFound:
    print( 'BluePrint "{0}" not found on Contractor'.format( args.blueprint_add ) )
    sys.exit( 1 )

  if not args.blueprint_add.startswith( 'mcp-' ):
    print( 'Must be a MCP blueprint' )
    sys.exit( 1 )

  blueprint = BluePrint()
  blueprint.name = args.blueprint_add[ 4: ]  # strip off the 'mcp-'
  blueprint.contractor_blueprint_id = args.blueprint_add
  blueprint.full_clean()
  blueprint.save()

  print( 'BluePrint "{0}" Created.'.format( blueprint.name ) )
  sys.exit( 0 )

if args.blueprint_remove:
  try:
    blueprint = BluePrint.objects.get( name=args.blueprint_remove )
  except BluePrint.DoesNotExist:
    print( 'BluePrint "{0}" not found in MCP'.format( args.blueprint_remove ) )
    sys.exit( 1 )

  blueprint.delete()
  print( 'BluePrint "{0}" deleted.'.format( args.blueprint_remove ) )
  sys.exit( 0 )

# site operations
if args.site_add:
  try:
    contractor_site = contractor.getSite( args.site_add )
  except cinp.client.NotFound:
    print( 'Site "{0}" not found on Contractor'.format( args.site_add ) )
    sys.exit( 1 )

  site = Site()
  site.name = args.site_add
  site.full_clean()
  site.save()

  print( 'Site "{0}" Created.'.format( site.name ) )
  sys.exit( 0 )

if args.site_remove:
  try:
    site = Site.objects.get( name=args.site_remove )
  except Site.DoesNotExist:
    print( 'Site "{0}" not found in MCP'.format( args.site_remove ) )
    sys.exit( 1 )

  site.delete()
  print( 'Site "{0}" deleted.'.format( args.site_remove ) )
  sys.exit( 0 )

# network operations
if args.network_add:
  try:
    network_id, address_block_id = args.network_add.split( ':' )
  except ValueError:
    print( 'network add value should be "<network id>:<address block id>"')
    sys.exit( 1 )

  try:
    contractor_network = contractor.getNetwork( network_id )
  except cinp.client.NotFound:
    print( 'Network "{0}" not found on Contractor'.format( network_id ) )
    sys.exit( 1 )

  if contractor_network[ 'site' ].split( ':' )[1] != site.name:
    print( 'Network "{0}" does not belong to site'.format( network_id ) )
    sys.exit( 1 )

  try:
    contractor_addressblock = contractor.getAddressBlock( address_block_id )
  except cinp.client.NotFound:
    print( 'AddressBlock "{0}" not found on Contractor'.format( address_block_id ) )
    sys.exit( 1 )

  for item in contractor_network[ 'address_block_list' ]:
    nab = contractor.cinp.get( item )
    if nab[ 'address_block' ] == '/api/v1/Utilities/AddressBlock:{0}:'.format( address_block_id ):
      break
  else:
    print( 'No Linkage between AddressBlock "{0}" and Network "{1}"'.format( address_block_id, network_id ) )
    sys.exit( 1 )

  network = Network()
  network.site = site
  network.name = contractor_network[ 'name' ]
  network.contractor_network_id = network_id
  network.contractor_addressblock_id = address_block_id
  network.monalythic = False
  network.size = contractor_addressblock[ 'size' ]
  network.full_clean()
  network.save()

  print( 'Network for Network "{0}" and Addressblock "{1}" Created.'.format( network_id, address_block_id ) )
  sys.exit( 0 )

if args.network_remove:
  try:
    network = Network.objects.get( name=args.network_remove )
  except Site.DoesNotExist:
    print( 'Network "{0}" not found in MCP'.format( args.network_remove ) )
    sys.exit( 1 )

  network.delete()
  print( 'Network "{0}" deleted.'.format( args.network_remove ) )
  sys.exit( 0 )

# dynamic resource options
if args.dynamic_resource_add:
  try:
    contractor_complex = contractor.getComplex( args.dynamic_resource_add )
  except cinp.client.NotFound:
    print( 'Complex "{0}" not found on Contractor'.format( args.dynamic_resource_add ) )
    sys.exit( 1 )

  dynamic_resource = DynamicResource()
  dynamic_resource.site = site
  dynamic_resource.name = contractor_complex[ 'name' ]
  dynamic_resource.description = '"{0}" complex in "{1}"'.format( contractor_complex[ 'name' ], site.name )
  dynamic_resource.complex_id = args.dynamic_resource_add
  dynamic_resource.full_clean()
  dynamic_resource.save()

  print( 'DynamicResource "{0}" Created.'.format( contractor_complex[ 'name' ] ) )
  sys.exit( 0 )

if args.dynamic_resource_remove:
  try:
    dynamic_resource = DynamicResource.objects.get( name=args.dynamic_resource_remove )
  except DynamicResource.DoesNotExist:
    print( 'Dynamic Resource "{0}" not found in MCP'.format( args.dynamic_resource_remove ) )
    sys.exit( 1 )

  dynamic_resource.delete()
  print( 'Dynamic Resource "{0}" deleted.'.format( args.dynamic_resource_remove ) )
  sys.exit( 0 )

# the temporary hack
if args.update_builtin:
  if site is None:
    print( 'specify site' )
    sys.exit( 1 )

  try:
    resource = DynamicResource.objects.get( site=site )
  except DynamicResource.DoesNotExist:
    print( 'no dynamic resources found' )
    sys.exit( 1 )

  try:
    project = Project.objects.get( name='_builtin_' )
  except Project.DoesNotExist:
    project = Project( name='_builtin_' )
    project.local_path = ''
    project.last_checked = datetime.now( timezone.utc )
    project.full_clean()
    project.save()

  for blueprint in BluePrint.objects.all():
    try:
      BuildResource.objects.get( build__project=project, blueprint=blueprint )
      continue
    except BuildResource.DoesNotExist:
      pass

    build = Build( name=blueprint.name, project=project )
    build.manual = False
    build.full_clean()
    build.save()

    br = BuildResource( name=blueprint.name, build=build, resource=resource )
    br.quantity = 1
    br.blueprint = blueprint
    br.autorun = False
    br.full_clean()
    br.save()

  for build in project.build_set.all():
    print( build )

  sys.exit( 0 )

print( 'No Action specified' )
sys.exit( 1 )
