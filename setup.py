#!/usr/bin/env python3

import glob
from distutils.core import setup
from distutils.command.build_py import build_py
from setuptools import find_packages
import os


class custom_build( build_py ):
    def run( self ):
      if os.path.lexists( 'mcp/settings.py' ):
        print( 'Moving settings.py asside...' )
        os.rename('mcp/settings.py', 'mcp/settings.py.tmp')

      open( 'mcp/settings.py', 'w' ).close()

      # build_py.run( self )
      # get .pys
      for package in self.packages:  # derived from build_py.run
        package_dir = self.get_package_dir(package)
        modules = self.find_package_modules(package, package_dir)
        for (package_, module, module_file) in modules:
          assert package == package_
          if os.path.basename( module_file ).endswith( '_test.py' ) or os.path.basename( module_file ) == 'tests.py':
            continue
          self.build_module(module, module_file, package)

      # get.htmls
      for src in glob.glob( 'mcp/templates/*/' ) + [ 'mcp/templates/' ]:
        src_dir = src[:-1]
        build_dir = '{0}/{1}'.format( self.build_lib, src_dir )
        for filename in glob.glob( '{0}/*.html'.format( src_dir ) ):
          filename = os.path.basename( filename )
          target = os.path.join(build_dir, filename)
          self.mkpath(os.path.dirname(target))
          self.copy_file(os.path.join(src_dir, filename), target, preserve_mode=False)

      # get initial_datas
      for src in glob.glob( 'mcp/*/fixtures/' ):
        src_dir = src[:-1]
        build_dir = '{0}/{1}'.format( self.build_lib, src_dir )
        for filename in glob.glob( '{0}/initial_data.json'.format( src_dir ) ):
          filename = os.path.basename( filename )
          target = os.path.join(build_dir, filename)
          self.mkpath(os.path.dirname(target))
          self.copy_file(os.path.join(src_dir, filename), target, preserve_mode=False)

      # other files
      for filename in []:
        src_dir = os.path.dirname( filename )
        build_dir = '{0}/{1}'.format( self.build_lib, src_dir )
        filename = os.path.basename( filename )
        target = os.path.join(build_dir, filename)
        self.mkpath(os.path.dirname(target))
        self.copy_file(os.path.join(src_dir, filename), target, preserve_mode=False)

      os.unlink( 'mcp/settings.py' )
      if os.path.lexists( 'mcp/settings.py.tmp' ):
        print( 'Moving settings.py back...' )
        os.rename('mcp/settings.py.tmp', 'mcp/settings.py')


setup( name='mcp-master',
       description='MCP',
       author='Peter Howe',
       author_email='peter.howe@virtustream.com',
       include_package_data=True,
       packages=find_packages(),
       cmdclass={ 'build_py': custom_build }
       )
