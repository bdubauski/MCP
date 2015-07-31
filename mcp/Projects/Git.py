import logging
import subprocess
import os
import shutil

GIT_CMD = '/usr/bin/git'

class Git( object ):
  def __init__( self, dir ):
    self.dir = dir

  def _execute( self, args, cwd=None ):
    logging.info( 'git: running "%s"' % args )

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

    if proc.returncode != 0:
      raise Exception( 'git returned "%s"' % proc.returncode )

    result = []
    for line in stdout.strip().splitlines():
      result.append( line.strip() )

    return result

  def setup( self, url ):  # use ~/.netrc file for auth.... for now
    self._execute( [ '--bare', 'clone', url ] )
    self._execute( [ '--bare', 'update-server-info' ] )
    os.path.rename( '%s/hooks/post-update.sample' % self.dir, '%s/hooks/post-update' % self.dir )

  def update( self ):
    self._execute( [ 'fetch', 'origin', 'master:master' ] )
    self._execute( [ '--bare', 'update-server-info' ] ) # should not have to run this... the hook/post-update should be doing this

  #http://gitready.com/intermediate/2009/02/13/list-remote-branches.html
  def branch_map( self ):
    result = {}
    branch_list = self._execute( [ 'branch', '--list', '--verbose' ] )
    for item in branch_list:
      ( name, hash, _ ) = item[2:].split( ' ', 2 )
      result[ name ] = hash

    return result

  def checkout( self, work_dir, branch ):
    if os.path.exists( work_dir ):
      shutil.rmtree( work_dir )

    os.makedirs( work_dir )

    self._execute( [ 'clone', self.dir, '-b', branch ], work_dir )
