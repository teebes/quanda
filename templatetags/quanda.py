from django import template
from django.core.urlresolvers import reverse

from ..quanda.utils import get_user_rep

register = template.Library()

def rep(username):
    return get_user_rep(username)

register.filter('rep', rep)

