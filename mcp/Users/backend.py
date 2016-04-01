from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User

from mcp.Users.models import MCPUser

class Backend( ModelBackend ):
  def authenticate( self, username=None, password=None ):
    try:
      user = User.objects.get( username=username )
    except User.DoesNotExist:
      return None

    try:
      user = user.mcpuser
    except MCPUser.DoesNotExist:
      pass

    if isinstance( user, MCPUser ):
      if user.login( password ):
        return user
      else:
        return None

    # no github, check local password
    if user.check_password( password ):
      return user

    # no luck
    return None
