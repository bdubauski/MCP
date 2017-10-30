import json
import urllib
import urllib2
import logging

class Slack( object ):
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
    self.user_name = 'mcp(%s)-%s' % ( site, proc ) if site else 'mcp-%s' % proc
    self.slack_api_base_url = 'https://slack.com/api'
    if proxy:
      self.opener = urllib2.build_opener( urllib2.ProxyHandler( { 'http': proxy, 'https': proxy } ) )
    else:
      self.opener = urllib2.build_opener( urllib2.ProxyHandler( {} ) )

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

    url = '%s/%s' % ( self.slack_api_base_url, 'chat.postMessage' )
    data = urllib.urlencode( data )
    try:
      resp = self.opener.open( url, data=data )
    except Exception as e:
      logging.warning( 'Slack: Got Exception "%s" when posting message' % e )
      return

    rc = resp.read()
    resp.close()
    try:
      rc = json.loads( rc )
    except TypeError:
      logging.warning( 'Slack: Response not valid JSON.' )
      return

    if 'ok' not in rc:
      logging.warning( 'Slack: Failed to post message "%s"' % rc )
      return
