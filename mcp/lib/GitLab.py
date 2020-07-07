import os
import logging

from gitlab import Gitlab
from gitlab.exceptions import GitlabAuthenticationError, GitlabGetError


class GitLabException( Exception ):
  pass


class GitLab():
  def __init__( self, host, proxy, private_token, group=None, project=None ):
    if proxy is not None:
      proxy_save = (  os.getenv( 'http_proxy' ), os.getenv( 'https_proxy' ) )
      os.environ[ 'http_proxy' ] = proxy
      os.environ[ 'https_proxy' ] = proxy
    else:
      proxy_save = None

    self.conn = Gitlab( host, private_token=private_token )

    self.conn.headers[ 'User-Agent' ] = 'MCP'

    try:
      self.conn.auth()
    except GitlabAuthenticationError:
      raise GitLabException( 'Unable to Login to gitlab' )

    if proxy_save is not None:
      os.environ[ 'http_proxy' ] = proxy_save[0]
      os.environ[ 'https_proxy' ] = proxy_save[1]

    self.group = group
    self.project = project
    self._glProject = None

  @property
  def _project( self ):
    if self._glProject is not None:
      return self._glProject

    self._glProject = self.conn.projects.get( self.project_id )  # raises GitlabGetError
    return self._glProject

  def _getMergeRequest( self, id ):
    try:
      return self._project.mergerequests.get( id )
    except GitlabGetError:
      return None

  def postCommitComment( self, commit_hash, comment ):
    logging.warning( 'Unable get Commit "{0}" of "{1}" in "{2}"'.format( commit_hash, self.repo, self.org ) )
    return

  def postCommitStatus( self, commit_hash, state ):
    return

  def postMergeComment( self, id, comment ):
    return

  def getMergeList( self ):
    return [ i.get_id() for i in self._project.mergerequests.list() ]

  def branchToMerge( self, branch_name ):
    if branch_name.startswith( '_MR' ):
      return int( branch_name[3:] )

    return None

  def mergeToBranch( self, merge ):
    return '_MR{0}'.format( merge )

  def mergeToRef( self, merge ):
    return 'refs/merge-requests/{0}/head'.format( merge )
