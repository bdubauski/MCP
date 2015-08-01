import logging
import subprocess

MAKE_CMD = '/usr/bin/make'

class Makefile( object ):
  def __init__( self, dir ):
    self.dir = dir

  def _execute( self, target ):
    logging.info( 'makefile: executing target "%s"' % target )

    try:
      args = [ MAKE_CMD, '-s', '-C', self.dir, target ]
      logging.debug( 'makefile: executing "%s"' % args )
      proc = subprocess.Popen( args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT )
      ( stdout, _ ) = proc.communicate()
    except Exception as e:
      raise Exception( 'Exception %s while makeing target "%s"' % ( e, target ) )

    if proc.returncode == 2:
      if stdout.startswith( 'make: *** No rule to make target' ):
        return []

      else:
        print '))))))))))))))) rc2: "%s"' % stdout

    logging.debug( 'make: rc: %s' % proc.returncode )
    logging.debug( 'make: output:\n----------\n%s\n---------' % stdout )

    if proc.returncode != 0:
      raise Exception( 'make returned "%s"' % proc.returncode )

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

  def depends( self, build ):
    return self._execute( '%s-depends' % build )

  def testDistros( self ):
    return self._execute( 'test-distros' )

  def packageDistros( self, type ): # type in dpkg, rpm, resource
    return self._execute( '%s-distros' % type )
