# Copyright Collab 2013-2018
# See LICENSE for details.

"""
Navigation template tags for the :py:mod:`admin_appmenu` application.
"""

from __future__ import unicode_literals

import logging

from django import template
from django.template import base, loader

from ..util import get_admin_site


register = template.Library()
logger = logging.getLogger(__name__)

class KgApp:
    def __init__(self, name, url):
        self.name = name;
        self.url = url;

train = KgApp("kg_train", "../../index.html")
test = KgApp("kg_test", "../../test.html")
viz = KgApp("kg_viz", "../../viz.html")

KG_APPS = [train, test, viz]

class AdminUserNavigationNode(template.Node):
    """
    Build navigation tree with the admin's :py:func:`get_app_list` and render
    the resulting context into the navigation template.
    """
    def render(self, context):
        data = None
        try:
            admin = get_admin_site()
            data = admin.get_app_list(context['request'])
        except (ValueError, KeyError):
            pass
        except Exception as e:  # pragma: no cover
            logger.exception(e)

        tpl = loader.get_template('admin_appmenu/navigation.html')
        return tpl.render({'nav_list': data})


@register.tag
def admin_navigation(parser, token):
    """
    Template tag that renders the main admin navigation tree based on the
    authenticated user's permissions.
    """
    # split_contents() knows not to split quoted strings.
    tag_name = token.split_contents()

    print(f"admin_navigation()")
    if len(tag_name) > 1:
        raise base.TemplateSyntaxError(
            '{} tag does not accept any argument(s): {}'.format(
            token.contents.split()[0],
            ', '.join(token.contents.split()[1:])
    ))

    return AdminUserNavigationNode()

@register.simple_tag
def mtw_navigation(parser, token):
    """
    Template tag that renders the main admin navigation tree based on the
    authenticated user's permissions.
    """
    # split_contents() knows not to split quoted strings.
    tag_name = token.split_contents()

    print(f"mtw_navigation()")
    if len(tag_name) > 1:
        raise base.TemplateSyntaxError(
            '{} tag does not accept any argument(s): {}'.format(
            token.contents.split()[0],
            ', '.join(token.contents.split()[1:])
    ))

    return AdminUserNavigationNode()

@register.filter
def my_custom_tag(arg1, arg2):
    return arg1 + arg2

@register.simple_tag
def kg_apps_list():
    print(f"kg_apps_list(), returning {KG_APPS.len}")
    return KG_APPS

@register.simple_tag
def my_class_tag(app):
    # my_instance = MyClass(value)
    return app.name
