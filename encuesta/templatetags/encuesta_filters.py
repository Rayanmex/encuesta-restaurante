# encuesta/templatetags/encuesta_filters.py
from django import template

register = template.Library()

@register.filter
def div(value, arg):
    """Divide value entre arg y retorna el resultado como float"""
    try:
        if value is None or arg is None or arg == 0:
            return 0
        return float(value) / float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def percentage(value, arg):
    """Calcula el porcentaje de value respecto a arg"""
    try:
        if value is None or arg is None or arg == 0:
            return 0
        return (float(value) / float(arg)) * 100
    except (ValueError, TypeError):
        return 0