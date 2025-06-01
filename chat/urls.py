from django.urls import path
from .views import *



urlpatterns = [
    path('chat/', get_or_create_chatroom),
    path('room/<str:room_id>/', chat_view),
    path('mark_message_as_read/', mark_as_read),
    path('chat/user/<str:user_id>/', get_user_chatrooms, name='get_user_chatrooms'),
    path('chat/unread/<str:user_id>/', get_unread_messages, name='get_unread_messages')
]