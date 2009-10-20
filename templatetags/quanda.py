from django import template
from django.core.urlresolvers import reverse

from ..quanda.utils import get_user_rep, smart_date

register = template.Library()

def rep(username):
    return get_user_rep(username)

def smartdate(event):
    return smart_date(event)
    
register.filter('rep', rep)
register.filter('smart_date', smartdate)

