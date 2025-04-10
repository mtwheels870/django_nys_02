# Copyright Collab 2016-2018

"""
Utilities.
"""

from __future__ import unicode_literals

from django.conf import settings
from django.utils.module_loading import import_string


def get_admin_site():
    """
    Get default or custom admin site instance.
    """
    print(f"get_admin_site()")
    path = getattr(settings, 'ADMIN_APPMENU_CLASS',
        'django.contrib.admin.site')
    return import_string(path)
