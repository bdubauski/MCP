import logging
import subprocess

MAKE_CMD = '/usr/bin/make'

class MakeException( Exception ):
  pass

class Makefile( object ):
  def __init__( self, dir ):
    self.dir = dir

  def _execute( self, target ):
    logging.info( 'makefile: executing target "%s"' % target )

    try:
      args = [ MAKE_CMD, 'MCP=1', '-s', '-C', self.dir, target ]
      logging.debug( 'makefile: executing "%s"' % args )
      proc = subprocess.Popen( args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT )
      ( stdout, _ ) = proc.communicate()
    except Exception as e:
      raise MakeException( 'Exception %s while makeing target "%s"' % ( e, target ) )

    logging.debug( 'make: rc: %s' % proc.returncode )
    logging.debug( 'make: output:\n----------\n%s\n---------' % stdout )

    if proc.returncode == 2:
      if stdout.startswith( 'make: *** No rule to make target' ):
        return []

    if proc.returncode != 0:
      raise MakeException( 'make returned "%s"' % proc.returncode )

    result = []
    for line in stdout.strip().splitlines():
      result += line.split()

    return result

  def autoBuilds( self ):
    return self._execute( 'auto-builds' )

  def manualBuilds( self ):
    return self._execute( 'manual-builds' )

  def resources( self, build ):
    return self._execute( '%s-resources' % build )

  def networks( self, build ):
    return self._execute( '%s-networks' % build )

  def depends( self, build ):
    return self._execute( '%s-depends' % build )

  def testDistros( self ):
    return self._execute( 'test-distros' )

  def packageDistros( self, type ): # type in dpkg, rpm, respkg, resource
    return self._execute( '%s-distros' % type )
