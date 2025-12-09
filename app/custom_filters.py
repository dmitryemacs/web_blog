# app/custom_filters.py
from flask import Markup

def nl2br(value):
    """Преобразует переносы строк в теги <br> для HTML"""
    if value:
        return Markup(value.replace('\n', '<br>\n'))
    return value
