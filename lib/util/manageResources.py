#!/usr/bin/env python3
import os

os.environ.setdefault( 'DJANGO_SETTINGS_MODULE', 'mcp.settings' )

import django
django.setup()

import sys
import argparse

from mcp.Resource.models import Site, DynamicResource


parser = argparse.ArgumentParser( description='resource manager - add/remove static and dynamic resources' )
parser.add_argument( '--dynamic-resource-blueprint', help='blueprint for the resources hosted on the resource complex' )

args = parser.parse_args()

site = Site.objects.get()


dr = DynamicResource( name=args.dynamic_resource_complex )
dr.description = 'Dynamic Resource "{0}"'.format( args.dynamic_resource_complex )
dr.blueprint = args.dynamic_resource_blueprint
dr.complex = args.dynamic_resource_complex
dr.site = site
dr.build_ahead_count = 0
dr.full_clean()
dr.save()

sys.exit( 0 )
