from django import template

register = template.Library()

@register.filter
def get_obj_attr(obj, attr_name):
    """
    Returns the attribute value of an object, safely handling relations or callables.
    """
    try:
        value = getattr(obj, attr_name)
        if callable(value):
            return value()
        return value
    except AttributeError:
        return ""
