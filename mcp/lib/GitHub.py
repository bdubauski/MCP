import os
import logging

from github import Github, GithubObject, BadCredentialsException, UnknownObjectException

class GitHubException( Exception ):
  pass

class GitHub( object ):
  def __init__( self, host, proxy, user, password, org=None, repo=None ):
    if proxy is not None:
      proxy_save = os.getenv( 'http_proxy' )
      os.environ[ 'http_proxy' ] = proxy
    else:
      proxy_save = None

    self.conn = Github( login_or_token=user, password=password, base_url=host, user_agent='MCP' )

    self.user = self.conn.get_user()

    try: # force communicatoin with Github
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
      self._ghRepo = self.conn.get_repo( '%s/%s' % ( self.owner, self.repo ) )
    else:
      self._ghRepo = self.conn.get_repo( '%s/%s' % ( self.org, self.repo ) )
    return self._ghRepo

  def getCommit( self, commit_hash ):
    return self.ghRepo.get_commit( commit_hash )

  def postCommitComment( self, commit_hash, comment, line=GithubObject.NotSet, path=GithubObject.NotSet, position=GithubObject.NotSet ):
    self.getCommit( commit_hash ).create_comment( comment, line, path, position )

  def postCommitStatus( self, commit_hash, state, target_url=GithubObject.NotSet, description=GithubObject.NotSet ):
    if state not in ( 'pending', 'success', 'error', 'failure' ):
      raise GitHubException( 'Invalid state' )

    try:
      self.getCommit( commit_hash ).create_status( state, target_url, description )
    except UnknownObjectException:
      logging.warning( 'Unable to set status on commit "%s" of "%s" in "%s", check permissions' % ( commit_hash, self.repo, self.org ) )

  def postPRComment( self, id, comment ):
    pr = self.ghRepo.get_pull( id )
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
    return self.ghRepo.get_pull( id ).user.login
