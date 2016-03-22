import os

from github import Github

class GitHub( object ):
  def __init__( self, host, proxy, user, password, org=None, repo=None ):
    if proxy is not None:
      proxy_save = os.getenv( 'http_proxy' )
      os.environ[ 'http_proxy' ] = proxy
    else:
      proxy_save = None

    self.conn = Github( login_or_token=user, password=password, base_url=host, user_agent='MCP' )
    self.user = self.conn.get_user()

    if proxy_save is not None:
      os.environ[ 'http_proxy' ] = proxy_save

    self.org = org
    self.repo = repo

  @property
  def ghRepo( self ):
    if self.org is None or self.repo is None:
      raise Exception( 'repo and org must be set' )

    try:
      if self._ghRepo:
        return self._ghRepo
    except AttributeError:
      pass

    self._ghRepo = self.conn.get_repo( '%s/%s' % ( self.org, self.repo ) )
    return self._ghRepo

  def postCommitComment( self, commit_hash, comment ):
    commit = self.ghRepo.get_commit( commit_hash )
    commit.create_comment( comment )

  def postPRComment( self, id, comment ):
    pr = self.ghRepo.get_pull( id )
    pr.create_issue_comment( comment )

  def getRepos( self ):
    result = []
    for item in self.user.get_repos():
      result.append( item.name )

    return result

  def getPullRequests( self ):
    return [ i.number for i in self.ghRepo.get_pulls() ]
