import os
import logging

from gitlab import Gitlab


class GitLabException( Exception ):
  pass


class GitLab():
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

    if proxy_save is not None:
      os.environ[ 'http_proxy' ] = proxy_save


https://python-gitlab.readthedocs.io/en/stable/api-usage.html#gitlab-gitlab-class
