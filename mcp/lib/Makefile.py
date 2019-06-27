import logging
import subprocess

MAKE_CMD = '/usr/bin/make'


class MakeException( Exception ):
  pass


class Makefile():
  def __init__( self, dir ):
    self.dir = dir

  def _execute( self, target ):
    logging.info( 'makefile: executing target "{0}"'.format( target ) )

    try:
      args = [ MAKE_CMD, 'MCP=1', '-s', '-C', self.dir, target ]
      logging.debug( 'makefile: executing "{0}"'.format( args ) )
      proc = subprocess.Popen( args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT )
      ( stdout, _ ) = proc.communicate()
    except Exception as e:
      raise MakeException( 'Exception {0} while makeing target "{1}"'.format( e, target ) )

    stdout = stdout.decode()
    logging.debug( 'make: rc: {0}'.format( proc.returncode ) )
    logging.debug( 'make: output:\n----------\n{0}\n---------'.format( stdout ) )

    if proc.returncode == 2:
      if stdout.startswith( 'make: *** No rule to make target' ):
        return []

    if proc.returncode != 0:
      logging.error( 'make returned "{0}":\n{1}'.format( proc.returncode, stdout ) )
      raise MakeException( 'make returned "{0}"'.format( proc.returncode ) )

    result = []
    for line in stdout.strip().splitlines():
      result += line.split()

    return result

  def lint( self ):
    try:
      self._execute( '-n' )
    except MakeException:
      return False

    return True

  def version( self ):
    try:
      tmp = self._execute( 'version' )
    except MakeException:
      return None

    if not tmp:
      return None
    else:
      return tmp[0]

  def autoBuilds( self ):
    return self._execute( 'auto-builds' )

  def manualBuilds( self ):
    return self._execute( 'manual-builds' )

  def resources( self, build ):
    return self._execute( '{0}-resources'.format( build ) )

  def networks( self, build ):
    return self._execute( '{0}-networks'.format( build ) )

  def depends( self, build ):
    return self._execute( '{0}-depends'.format( build ) )

  def testDistros( self ):
    return self._execute( 'test-distros' )

  def docDistros( self ):
    return self._execute( 'doc-distros' )

  def packageDistros( self, type ):  # type in dpkg, rpm, respkg, resource
    return self._execute( '{0}-distros'.format( type ) )
