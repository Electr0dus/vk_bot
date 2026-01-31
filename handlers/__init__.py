from .chat import chat_labeler
from .admin import admin_labeler
from .ping import labeler
# Если использовать глобальный лейблер, то все хендлеры будут зарегистрированы в том же порядке, в котором они были импортированы

__all__ = ("admin_labeler", "chat_labeler", "labeler")