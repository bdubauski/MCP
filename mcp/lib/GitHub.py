import os

from github import Github

class GitHub( object ):
  def __init__( self, host, proxy, user, password ):
    if proxy is not None:
      proxy_save = os.getenv( 'http_proxy' )
      os.environ[ 'http_proxy' ] = proxy
    else:
      proxy_save = None

    self.conn = Github( login_or_token=user, password=password, base_url=host, user_agent='MCP' )
    self.user = self.conn.get_user()

    if proxy_save is not None:
      os.environ[ 'http_proxy' ] = proxy_save

  def postComment( self, org, repo, commit_hash, comment ):
    repo = self.conn.get_repo( '%s/%s' % ( org, repo ) )
    commit = repo.get_commit( commit_hash )
    commit.create_comment( comment )

  def getRepos( self ):
    result = []
    for item in self.user.get_repos():
      result.append( item.name )

    return result
