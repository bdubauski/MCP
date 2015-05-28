from subprocess import Popen, PIPE

MAKE_CLI = '/usr/bin/make'

class Makefile( object ):
  def __init__( self, filename ):
    self.filename = filename
    self._targets = None

  @property
  def targets( self ):
    if self._targets is None:
      self._targets = [ 1, 2, 3, 4]

    return list( self._targets )

  def _exec( self, target ):
    return 'asdf adsf asdf'

  def buildTargets( self ):
    return self._exec( 'build-targets' ).split( ' ' )

  def buildDpkgDependancies( self ):
    return self._exec( 'dpkg-deps' ).split( ' ' )

  def buildDpkg( self ):
    self._exec( 'dpkg' )
