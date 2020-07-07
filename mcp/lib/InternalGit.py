import logging
import subprocess
import os
import shutil

GIT_CMD = '/usr/bin/git'


class InternalGit():
  def __init__( self, dir, release_branch ):
    self.dir = dir
    self.release_branch = release_branch

  def _execute( self, args, cwd=None ):
    logging.debug( 'git: running "{0}"'.format( args ) )

    try:
      if cwd is None:
        args = [ GIT_CMD, '--git-dir', self.dir ] + args
      else:
        args = [ GIT_CMD ] + args
      logging.debug( 'git: executing "{0}"'.format( args ) )
      proc = subprocess.Popen( args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=cwd )
      ( stdout, _ ) = proc.communicate()
    except Exception as e:
      raise Exception( 'Exception {0} while executing "{1}"'.format( e, args ) )

    stdout = stdout.decode()
    logging.debug( 'git: rc: {0}'.format( proc.returncode ) )
    logging.debug( 'git: output:\n----------\n{0}\n---------'.format( stdout ) )

    if proc.returncode != 0:
      raise Exception( 'git returned "{0}"'.format( proc.returncode ) )

    result = []
    for line in stdout.strip().splitlines():
      result.append( line.strip() )

    return result

  def setup( self, url ):
    parent_path = '/'.join( self.dir.split( '/' )[ :-1 ] )

    try:
      os.makedirs( parent_path )

    except OSError as e:
      if e.errno == 17:  # allready exists
        pass

      else:
        raise e

    self._execute( [ 'clone', '--bare', url ], cwd=parent_path )
    self._execute( [ 'update-server-info' ] )
    os.rename( '{0}/hooks/post-update.sample'.format( self.dir ), '{0}/hooks/post-update'.format( self.dir ) )

  def update( self ):
    self._execute( [ 'fetch', 'origin', '+refs/heads/*:refs/heads/*', '--force' ] )
    self._execute( [ 'update-server-info' ] )  # should not have to run this... the hook/post-update should be doing this

  def fetch_branch( self, remote_name, local_name ):
    self._execute( [ 'fetch', 'origin', '{0}:{1}'.format( remote_name, local_name ), '--force' ] )
    self._execute( [ 'update-server-info' ] )  # should not have to run this... the hook/post-update should be doing this

  def remove_branch( self, branch ):
    if branch == self.release_branch:
      raise Exception( 'Release Branch "{0}" is not Deleteable'.format( self.release_branch ) )

    self._execute( [ 'branch', '-D', branch ] )

  def ref_map( self ):
    result = {}
    ref_list = self._execute( [ 'show-ref' ] )
    for item in ref_list:
      ( ref_hash, ref ) = item.split()
      if not ref.startswith( 'refs/heads/' ):
        continue

      result[ ref[11:] ] = ref_hash

    return result

  def tag( self, version, comment ):
    try:
      self._execute( [ 'tag', '-a', version, '-m', comment ] )
    except Exception:
      return

    self._execute( [ 'push', 'origin', version ] )

  def checkout( self, work_dir, branch ):
    if os.path.exists( work_dir ):
      shutil.rmtree( work_dir )

    os.makedirs( work_dir )

    self._execute( [ 'clone', self.dir, '-b', branch ], work_dir )
