import os
import logging

from github import Github, GithubObject, BadCredentialsException, UnknownObjectException


class GitHubException( Exception ):
  pass


class GitHub():
  def __init__( self, host, proxy, user, password, org, repo ):
    if proxy is not None:
      proxy_save = (  os.getenv( 'http_proxy' ), os.getenv( 'https_proxy' ) )
      os.environ[ 'http_proxy' ] = proxy
    else:
      proxy_save = None

    if password is not None:
      self.conn = Github( login_or_token=user, password=password, base_url=host, user_agent='MCP' )
    else:
      self.conn = Github( login_or_token=user, base_url=host, user_agent='MCP' )

    self.user = self.conn.get_user()

    try:  # force communicatoin with Github
      self.user.type
    except BadCredentialsException:
      raise GitHubException( 'Unable to Login to github' )

    if proxy_save is not None:
      os.environ[ 'http_proxy' ] = proxy_save[0]
      os.environ[ 'https_proxy' ] = proxy_save[1]

    self.org = org
    self.repo = repo
    self._ghRepo = None

  @property
  def _repo( self ):
    if self._ghRepo is not None:
      return self._ghRepo

    self._ghRepo = self.conn.get_repo( '{0}/{1}'.format( self.org, self.repo ) )

    return self._ghRepo

  def _getCommit( self, commit_hash ):
    try:
      return self._getRepo().get_commit( commit_hash )
    except UnknownObjectException:
      return None

  def _getPullRequest( self, id ):
    try:
      return self._getRepo().get_pull( id )
    except UnknownObjectException:
      return None

  def postCommitComment( self, commit_hash, comment ):
    commit = self._getCommit( commit_hash )
    if commit is None:
      logging.warning( 'Unable get Commit "{0}" of "{1}" in "{2}"'.format( commit_hash, self.repo, self.org ) )
      return

    if len( comment ) > 65000:  # max comment max length is 65536
      comment = comment[ 0:32000 ] + '\n\n ... (comment to long, trimmed) ... \n\n' + comment[ -32000: ]

    commit.create_comment( comment, GithubObject.NotSet, GithubObject.NotSet, GithubObject.NotSet )

  def postCommitStatus( self, commit_hash, branch, state, description=None ):
    if state not in ( 'pending', 'success', 'error', 'failure' ):
      raise GitHubException( 'Invalid state' )

    commit = self._getCommit( commit_hash )
    if commit is None:
      logging.warning( 'Unable get Commit "{0}" of "{1}" in "{2}"'.format( commit_hash, self.repo, self.org ) )
      return

    if description is None:
      description = GithubObject.NotSet

    try:
      commit.create_status( state, GithubObject.NotSet, description, 'MCP Tests' )  # state, target_url, description, context
    except UnknownObjectException:
      logging.warning( 'Unable to set status on commit "{0}" of "{1}" in "{2}", check permissions'.format( commit_hash, self.repo, self.org ) )

  def postMergeComment( self, id, comment ):
    pr = self._getPullRequest( id )
    if pr is None:
      logging.warning( 'Unable get PR "{0}" of "{1}" in "{2}"'.format( id, self.repo, self.org ) )
      return

    pr.create_issue_comment( comment )

  def getMergeList( self ):
    return [ i.number for i in self._repo.get_pulls() ]

  def branchToMerge( self, branch_name ):
    if branch_name.startswith( '_PR' ):
      return int( branch_name[3:] )

    return None

  def mergeToBranch( self, merge ):
    return '_PR{0}'.format( merge )

  def mergeToRef( self, merge ):
    return 'refs/pull/{0}/head'.format( merge )
