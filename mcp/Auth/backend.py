from django.contrib.auth.backends import ModelBackend
from mcp.Auth.models import MCPUser

class Backend( ModelBackend ):
  def authenticate( self, username=None, password=None ):
    try:
      user = MCPUser.objects.get( username=username )
    except MCPUser.DoesNotExist:
      return None

    print 'trying github...'
    if user.github_user:
      print '  github...'
      if user.github_auth( password ):
        print 'Got it'
        return user
      else:
        return None

    print 'trying local...'
    # no github, check local password
    if user.check_password( password ):
      return user

    # no luck
    return None
