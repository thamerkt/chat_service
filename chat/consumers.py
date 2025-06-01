import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer

class NotificationConsumer(WebsocketConsumer):
    def connect(self):
        user_id = self.scope['url_route']['kwargs'].get('user_id') or self.scope.get('user_id')
        if not user_id:
            self.close()
            return

        self.user_id = str(user_id)
        self.user_channel_group = f'user_{self.user_id}'
        print(f'[Notification] Connected user ID: {self.user_id}')

        async_to_sync(self.channel_layer.group_add)(
            self.user_channel_group,
            self.channel_name
        )

        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.user_channel_group,
            self.channel_name
        )

    def receive(self, text_data):
        pass  # No-op

    def notify_message(self, event):
        self.send(text_data=json.dumps({
            'type': 'notify_message',
            'message': event['message'],
        }))
import json
import logging
from datetime import datetime, timezone
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from .models import ChatRoom, Message
from .gemini_helper import GeminiModerator

logger = logging.getLogger(__name__)
connected_users = {}  # {user_id: channel_name}

class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.chatroom_id = self.scope['url_route']['kwargs'].get('room_id')
        self.user_id = self.scope['url_route']['kwargs'].get('user_id')

        if not self.chatroom_id or not self.user_id:
            self.close()
            return

        self.user_id = str(self.user_id)

        try:
            self.chatroom = ChatRoom.objects.get(id=self.chatroom_id)
            if self.user_id not in [str(member) for member in self.chatroom.members]:
                self.close()
                return
        except ChatRoom.DoesNotExist:
            self.close()
            return

        self.room_group_name = f'chat_{self.chatroom_id}'
        connected_users[self.user_id] = self.channel_name

        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )

        self.accept()

    def disconnect(self, close_code):
        connected_users.pop(self.user_id, None)
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    def receive(self, text_data):
        try:
            data = json.loads(text_data)
            action = data.get('action')

            if action == 'ping':
                self.send(text_data=json.dumps({'type': 'pong'}))
                return

            if action == 'message':
                self.handle_message(data)
            elif action == 'typing':
                self.handle_typing(data)

        except json.JSONDecodeError:
            logger.error("Invalid JSON received")
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)

    def handle_message(self, data):
        content = data.get('content')
        receiver_id = str(data.get('receiver_id'))
        temp_id = data.get('temp_id')

        if not content or not receiver_id:
            return

        GeminiHelper = GeminiModerator()
        is_safe = GeminiHelper.check_message(content)
        if not is_safe.get("allowed"):
            content = "Message contains sensitive content."

        message = Message.objects.create(
            content=content,
            sender_id=self.user_id,
            receiver_id=receiver_id,
            room=self.chatroom,
            created_at=datetime.now(timezone.utc),
            is_read=receiver_id in connected_users
        )

        message_data = {
            'type': 'chat_message',
            'message': {
                'id': message.id,
                'temp_id': temp_id,
                'content': message.content,
                'sender_id': self.user_id,
                'receiver_id': receiver_id,
                'created_at': message.created_at.isoformat(),
                'is_read': message.is_read,
                'room': str(self.chatroom.id)
            }
        }

        # Send to all users in the chat room
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            message_data
        )

        # Notify the receiver in NotificationConsumer if they're not connected to chat
        if receiver_id != self.user_id and receiver_id not in connected_users:
            async_to_sync(self.channel_layer.group_send)(  # ✅ Corrected from `.send()` to `.group_send()`
                f'user_{receiver_id}',
                {
                    'type': 'notify_message',
                    'message': message_data['message']
                }
            )

    def handle_typing(self, data):
        typing_data = {
            'type': 'typing_status',
            'user_id': self.user_id,
            'typing': data.get('typing', False)
        }

        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            typing_data
        )

    def chat_message(self, event):
        self.send(text_data=json.dumps(event))

    def typing_status(self, event):
        self.send(text_data=json.dumps(event))

    def notify_message(self, event):
        self.send(text_data=json.dumps({
            'type': 'notification',
            'message': event['message']
        }))
