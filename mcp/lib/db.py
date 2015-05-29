APP_LIST = ( 'Projects', 'Processor', 'Resources', 'auth', 'sessions', 'contenttypes', 'admin', 'django' )

class MCPRouter( object ):
  def db_for_read( self, model, **hints ):
    if model._meta.app_label in APP_LIST:
      return 'mcp'

    return None

  def db_for_write( self, model, **hints ):
    if model._meta.app_label in APP_LIST:
      return 'mcp'

    return None

  def allow_relation( self, obj1, obj2, **hints ):
    if obj1._meta.app_label in APP_LIST or obj2._meta.app_label in APP_LIST:
     return True

    return None

  def allow_syncdb( self, db, model ):
    if db == 'mcp':
      return model._meta.app_label in APP_LIST

    elif model._meta.app_label in APP_LIST:
      return False

    return None
