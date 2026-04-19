from django import template

register = template.Library()

@register.filter
def get_obj_attr(obj, attr):
    """
    Gets an attribute of an object dynamically from a string name.
    Usage: {{ obj|get_obj_attr:field_name }}
    """
    try:
        if hasattr(obj, attr):
            # Check if it's a callable like a method, some model fields like get_FOO_display are callable
            attribute = getattr(obj, attr)
            if callable(attribute):
                try:
                    return attribute()
                except TypeError:
                    # If it needs arguments, we can't call it like this.
                    return attribute
            return attribute
        elif isinstance(obj, dict):
            return obj.get(attr, '')
        else:
            return ''
    except Exception:
        return ''
