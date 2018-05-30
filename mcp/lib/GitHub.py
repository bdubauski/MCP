import os
import logging

from github import Github, GithubObject, BadCredentialsException, UnknownObjectException


class GitHubException( Exception ):
  pass


class GitHub():
  def __init__( self, host, proxy, user, password, org=None, repo=None ):
    if proxy is not None:
      proxy_save = os.getenv( 'http_proxy' )
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
      os.environ[ 'http_proxy' ] = proxy_save

    self.org = org
    self.repo = repo
    self.owner = None
    self._ghRepo = None

  def setOwner( self, owner=None ):
    self.owner = owner
    self._ghRepo = None

  @property
  def ghRepo( self ):
    if self.org is None or self.repo is None:
      raise Exception( 'repo and org must be set' )

    if self._ghRepo is not None:
      return self._ghRepo

    if self.owner is not None:
      self._ghRepo = self.conn.get_repo( '{0}/{1}'.format( self.owner, self.repo ) )
    else:
      self._ghRepo = self.conn.get_repo( '{0}/{1}'.format( self.org, self.repo ) )
    return self._ghRepo

  def getCommit( self, commit_hash ):
    try:
      return self.ghRepo.get_commit( commit_hash )
    except UnknownObjectException:
      return None

  def getPR( self, id ):
    try:
      return self.ghRepo.get_pull( id )
    except UnknownObjectException:
      return None

  def postCommitComment( self, commit_hash, comment, line=GithubObject.NotSet, path=GithubObject.NotSet, position=GithubObject.NotSet ):
    commit = self.getCommit( commit_hash )
    if commit is None:
      logging.warning( 'Unable get Commit "{0}" of "{1}" in "{2}"'.format( commit_hash, self.repo, self.org ) )
      return

    commit.create_comment( comment, line, path, position )

  def postCommitStatus( self, commit_hash, state, target_url=GithubObject.NotSet, description=GithubObject.NotSet ):
    if state not in ( 'pending', 'success', 'error', 'failure' ):
      raise GitHubException( 'Invalid state' )

    commit = self.getCommit( commit_hash )
    if commit is None:
      logging.warning( 'Unable get Commit "{0}" of "{1}" in "{2}"'.format( commit_hash, self.repo, self.org ) )
      return

    try:
      commit.create_status( state, target_url, description )
    except UnknownObjectException:
      logging.warning( 'Unable to set status on commit "{0}" of "{1}" in "{2}", check permissions'.format( commit_hash, self.repo, self.org ) )

  def postPRComment( self, id, comment ):
    pr = self.getPR( id )
    if pr is None:
      logging.warning( 'Unable get PR "{0}" of "{1}" in "{2}"'.format( id, self.repo, self.org ) )
      return

    pr.create_issue_comment( comment )

  def getRepos( self ):
    result = {}
    for org in self.user.get_orgs():
      wrk = []
      for repo in org.get_repos():
        wrk.append( repo.name )

      result[ org.login ] = wrk

    return result

  def getPullRequests( self ):
    return [ i.number for i in self.ghRepo.get_pulls() ]

  def getPullRequestOwner( self, id ):
    pr = self.getPR( id )
    if pr is None:
      logging.warning( 'Unable get PR "{0}" of "{1}" in "{2}"'.format( id, self.repo, self.org ) )
      return None

    return pr.user.login
