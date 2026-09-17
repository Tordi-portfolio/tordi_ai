from django.urls import path
from . import views

app_name = "chat"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("chat/new/", views.new_chat, name="new_chat"),
    path("chat/<int:conversation_id>/send/", views.send_message, name="send_message"),
    path("chat/message/<int:message_id>/edit/", views.edit_message, name="edit_message"),
    path("chat/<int:conversation_id>/rename/", views.rename_chat, name="rename_chat"),
    path("chat/<int:conversation_id>/delete/", views.delete_chat, name="delete_chat"),
    path("chat/<int:conversation_id>/pin/", views.pin_chat, name="pin_chat"),
]
