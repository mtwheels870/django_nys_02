#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2025, PINP01NT, LLC
#
# https://pinp01nt.com/
#
# All rights reserved.
#
"""
Django's command-line utility for administrative tasks.

Authors: Michael T. Wheeler (mike@pinp01nt.com)

"""
import os
import sys


def main():
    """Run administrative tasks."""
    # PRODUCTION CHANGE (should be good as this...)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_nys_02.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
