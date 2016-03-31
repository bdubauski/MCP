from django.db import models
from django.conf import settings
from django.contrib.auth.models import User

from mcp.lib.GitHub import GitHub, GitHubException

class MCPUser( User ):
  github_user = models.CharField( max_length=100, blank=True, null=True )

  def github_auth( self, password ):
    if self.github_user is None:
      return False

    try:
      GitHub( settings.GITHUB_API_HOST, settings.GITHUB_PROXY, self.github_user, password )
    except GitHubException:
      return False

    return True
