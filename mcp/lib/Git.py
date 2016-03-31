import logging
import subprocess
import os
import shutil

GIT_CMD = '/usr/bin/git'

class Git( object ):
  def __init__( self, dir ):
    self.dir = dir

  def _execute( self, args, cwd=None ):
    logging.debug( 'git: running "%s"' % args )

    try:
      if cwd is None:
        args = [ GIT_CMD, '--git-dir', self.dir ] + args
      else:
        args = [ GIT_CMD ] + args
      logging.debug( 'git: executing "%s"' % args )
      proc = subprocess.Popen( args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=cwd )
      ( stdout, _ ) = proc.communicate()
    except Exception as e:
      raise Exception( 'Exception %s while executing "%s"' % ( e, args ) )

    logging.debug( 'git: rc: %s' % proc.returncode )
    logging.debug( 'git: output:\n----------\n%s\n---------' % stdout )

    if proc.returncode != 0:
      raise Exception( 'git returned "%s"' % proc.returncode )

    result = []
    for line in stdout.strip().splitlines():
      result.append( line.strip() )

    return result

  def setup( self, url, parent_path ):
    self._execute( [ 'clone', '--bare', url ], cwd=parent_path )
    self._execute( [ 'update-server-info' ] )
    os.rename( '%s/hooks/post-update.sample' % self.dir, '%s/hooks/post-update' % self.dir )

  def update( self ):
    self._execute( [ 'fetch', 'origin', '+refs/heads/*:refs/heads/*', '--force' ] )
    self._execute( [ 'update-server-info' ] ) # should not have to run this... the hook/post-update should be doing this

  def fetch_branch( self, remote_name, local_name ):
    self._execute( [ 'fetch', 'origin', '%s:%s' % ( remote_name, local_name ), '--force' ] )
    self._execute( [ 'update-server-info' ] ) # should not have to run this... the hook/post-update should be doing this

  def remove_branch( self, branch ):
    if branch == 'master':
      raise Exception( 'Master Branch is not Deleteable' )

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

  def checkout( self, work_dir, branch ):
    if os.path.exists( work_dir ):
      shutil.rmtree( work_dir )

    os.makedirs( work_dir )

    self._execute( [ 'clone', self.dir, '-b', branch ], work_dir )
