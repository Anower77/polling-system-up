"""
WSGI config for polling project.
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'polling.settings')

application = get_wsgi_application()

# For Vercel deployment
app = application 