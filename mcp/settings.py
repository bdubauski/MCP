# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'w4hhv%e7yq8(-$u8w3e2w5_^4q749(*mb-#-j!1ms*w9s5f@x='

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []

MCP_HOST_NAME = 'http://mcp.mcp.test'
MCP_PROXY = None

# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'cinp',
    'mcp.Processor',
    'mcp.Projects',
    'mcp.Resources',
    'plato.Base',
    'plato.Pod',
    'plato.DataCenter',
    'plato.Asset',
    'plato.Config',
    'plato.Device',
    'plato.Network',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

ROOT_URLCONF = 'mcp.urls'

from plato.settings import PROVISIONING_PROFILES, PLATO_HOST_NAME

# Database
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases

DATABASES = {
  'default': {
      'ENGINE': 'django.db.backends.postgresql_psycopg2',
      'NAME': 'plato',
      'USER': 'plato',
      'PASSWORD': 'plato',
      'HOST': '127.0.0.1',
      'PORT': '',
  },
  'mcp': {
    'ENGINE': 'django.db.backends.postgresql_psycopg2',
    'NAME': 'mcp',
    'USER': 'mcp',
    'PASSWORD': 'mcp',
    'HOST': '127.0.0.1',
    'PORT': '',
  }
}


DATABASE_ROUTERS = [ 'mcp.lib.db.MCPRouter' ]

# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'America/Denver'

USE_I18N = True

USE_L10N = True

USE_TZ = True

STATIC_URL = '/static/'
