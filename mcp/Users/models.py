from django.db import models
from django.conf import settings
from django.utils.crypto import get_random_string
from django.contrib.auth.models import User, Group

from mcp.Project.models import Project, GitHubProject
from mcp.lib.libGitHub import GitHub, GitHubException

class MCPUser( User ):
  """
  MCPUser is used to auth against MCP, and includes github and slack info
  """
  projects = models.ManyToManyField( Project, through='MCPUserProject', help_text='' ) # github logins will reset this upon login
  github_username = models.CharField( max_length=100, blank=True, null=True ) # to auth aginst github
  slack_handle = models.CharField( max_length=100, blank=True, null=True ) # to notify when a job complets

  github_oath = models.CharField( max_length=100, blank=True, null=True ) # oath token from github
  github_orgs = models.TextField( blank=True, null=True ) # if set, will limit the orgs visable to this user, coma delimited

  def login( self, password ):  # if this fails do not try any other login stuff, it failed period.
    if self.github_username is None:
      return False

    gh = None
    try:
      gh = GitHub( settings.GITHUB_API_HOST, settings.GITHUB_PROXY, self.github_username, password )
    except GitHubException:
      return False

    if gh is not None:
      self.projects.clear()
      repo_map = gh.getRepos()
      for org in repo_map:
        for repo in repo_map[ org ]:
          try:
            project = GitHubProject.objects.get( _org=org, _repo=repo )
          except GitHubProject.DoesNotExist:
            continue

          usrprj = MCPUserProject()
          usrprj.user = self
          usrprj.project = project
          usrprj.save()

    return True

  @staticmethod
  def getProfile( user ):
    if user.is_anonymous():
      return False

    try:
      user = MCPUser.objects.get( username=user.username )
    except MCPUser.DoesNotExist:
      return False

    return { 'github_username': user.github_username, 'slack_handle': user.slack_handle, 'first_name': user.first_name, 'last_name': user.last_name, 'email': user.email }

  @staticmethod
  def updateProfile( user, first_name, last_name, email, slack_handle ):
    if user.is_anonymous():
      return False

    try:
      user = MCPUser.objects.get( username=user.username )
    except MCPUser.DoesNotExist:
      return False

    user.first_name = first_name
    user.last_name = last_name
    user.email = email
    user.slack_handle = slack_handle

    user.save()
    return True

  @staticmethod
  def selfRegister( user, github_username=None, github_password=None ):
    """
    self Register a user, returns an array with error strigs if there are errors
    return True on success
    """
    if not user.is_anonymous():
      return [ 'Must logout before Self Registering' ]

    user = None
    try:
      user = User.objects.get( username=github_username )
    except User.DoesNotExist:
      pass

    if user is not None:
      return [ 'User "%s" is Allread Registered' % github_username ]

    try:
      GitHub( settings.GITHUB_API_HOST, settings.GITHUB_PROXY, github_username, github_password )
    except GitHubException:
      return [ 'GitHub Username and/or Password is incorrect' ]

    user = MCPUser()
    user.username = github_username
    user.github_username = github_username
    user.set_password( get_random_string( length=20 ) )
    user.save()

    user.groups.add( Group.objects.get( name=settings.SELFREGISTER_USER_GROUP ) )

    return None

  def __unicode__( self ):
    return 'MCPUser User "%s"' % self.username

  class API:
    not_allowed_methods = ( 'LIST', 'UPDATE', 'CREATE', 'DELETE' )
    show_fields = ( 'username', 'first_name', 'last_name', 'email', 'github_username', 'slack_handle', )
    actions = {
                'getProfile': ( { 'type': 'Map' }, ( { 'type': '_USER_' }, ) ),
                'updateProfile': ( { 'type': 'Boolean' }, ( { 'type': '_USER_' }, { 'type': 'String' }, { 'type': 'String' }, { 'type': 'String' }, { 'type': 'String' } ) ),
                'selfRegister': ( { 'type': 'StringList' }, (  { 'type': '_USER_' }, { 'type': 'String' }, { 'type': 'String' } ) )
              }

class MCPUserProject( models.Model ):
  user = models.ForeignKey( MCPUser, on_delete=models.CASCADE )
  project = models.ForeignKey( Project, on_delete=models.CASCADE )

  def __unicode__( self ):
    return 'MCPUserProject for User "%s" Project "%s"' % ( self.user, self.project )

  class Meta:
    unique_together = ( ( 'user', 'project' ), )
