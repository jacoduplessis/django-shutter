from .base import *

DEBUG = True

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.db': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        'django.server': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        'django.template': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'tagger': {
            'handlers': ['console'],
            'level': 'DEBUG',
        }
    },
}