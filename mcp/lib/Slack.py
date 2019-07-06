import json
import logging
from urllib import request, parse

from django.conf import settings


def getSlack( service ):
  return Slack( service, settings.SLACK_API_TOKEN, settings.SLACK_CHANNEL, settings.SITE_NAME, settings.SLACK_PROXY )


class Slack():
  NOTSET = ':loudspeaker:'
  DEBUG = ':speaker:'
  INFO = ':information_source:'
  WARNING = ':warning:'
  ERROR = ':exclamation:'
  CRITICAL = ':boom:'
  SUCCESS = ':+1:'
  DONE = ':checkered_flag:'

  def __init__( self, proc, api_token, channel_name, site=None, proxy=None ):
    self.api_token = api_token
    self.channel_name = channel_name
    self.user_name = 'mcp({0})-{1}'.format( site, proc ) if site else 'mcp-{0}'.format( proc )
    self.slack_api_base_url = 'https://slack.com/api'
    if proxy:
      self.opener = request.build_opener( request.ProxyHandler( { 'http': proxy, 'https': proxy } ) )
    else:
      self.opener = request.build_opener( request.ProxyHandler( {} ) )

  def post_message( self, message, emoji=NOTSET ):
    if self.api_token is None:
      return

    data = {
        'token': self.api_token,
        'channel': self.channel_name,
        'username': self.user_name,
        'text': message,
        'icon_emoji': emoji
    }

    url = '{0}/{1}'.format( self.slack_api_base_url, 'chat.postMessage' )
    data = parse.urlencode( data )
    try:
      resp = self.opener.open( url, data=data.encode() )
    except Exception as e:
      logging.warning( 'Slack: Got Exception "{0}" when posting message'.format( e ) )
      return

    rc = resp.read()
    resp.close()
    try:
      rc = json.loads( rc )
    except TypeError:
      logging.warning( 'Slack: Response not valid JSON.' )
      return

    if 'ok' not in rc:
      logging.warning( 'Slack: Failed to post message {0}'.format( rc ) )
      return
