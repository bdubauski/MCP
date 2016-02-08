from github import Github

class GitHub( object ):
  def __init__( self, host, user, password ):
    self.conn = Github( login_or_token=user, password=password, base_url=host, user_agent='MCP' )
    self.user = self.conn.get_user()

  def postComment( self, repo_name, commit_hash, comment ):
    repo = self.comm.get_repo( repo_name )
    commit = repo.get_commit( commit_hash )
    commit.create_comment( comment )
