from django.db import models

class ChatRoom(models.Model):
    id = models.CharField(primary_key=True, max_length=128, unique=True)
    members =models.JSONField() # liste d'IDs utilisateurs stockés en JSON, ex: [1, 42]

class Message(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender_id = models.CharField(max_length=128)
    receiver_id = models.CharField(max_length=128)
    content = models.CharField(max_length=300)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
