from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import ChatRoom, Message
from .serializers import MessageSerializer


@api_view(['POST'])
def get_or_create_chatroom(request):
    data = request.data
    sender_id = str(data.get('sender_id'))
    receiver_id = str(data.get('receiver_id'))

    if sender_id == receiver_id:
        return Response({'message': 'Cannot chat with yourself.'}, status=status.HTTP_406_NOT_ACCEPTABLE)

    # Chercher une chatroom avec les 2 membres (ordre non important)
    chatrooms = ChatRoom.objects.filter(members__contains=[sender_id]).filter(members__contains=[receiver_id])

    for room in chatrooms:
        if set(room.members) == set([sender_id, receiver_id]):
            return Response({'chatroom': room.id, 'members': room.members})

    # Créer une nouvelle chatroom
    chatroom = ChatRoom.objects.create(id=f'room_{sender_id}_{receiver_id}', members=[sender_id, receiver_id])
    return Response({'chatroom': chatroom.id, 'members': chatroom.members})


@api_view(['GET'])
def chat_view(request, room_id, user_id="cc327b55-1cfe-4be8-ae0c-c469bc2848a1"):
    try:
        chatroom = ChatRoom.objects.get(id=room_id)
    except ChatRoom.DoesNotExist:
        return Response({'detail': 'ChatRoom not found.'}, status=status.HTTP_404_NOT_FOUND)

    # Check if user_id is in chatroom members JSON list
    if str(user_id) not in chatroom.members:
        return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

    # Mark messages as read for this user
    Message.objects.filter(receiver_id=str(user_id), room=chatroom, is_read=False).update(is_read=True)

    # Get all messages in this chatroom ordered by created_at
    messages = Message.objects.filter(room=chatroom).order_by('created_at')
    serializer = MessageSerializer(messages, many=True)

    # Return chatroom info + messages
    return Response({
        'chatroom': {
            'id': chatroom.id,
            'members': chatroom.members,
        },
        'messages': serializer.data,
    })


@api_view(['POST'])
def mark_as_read(request):
    msg_id = request.data.get('msg_id')

    try:
        message = Message.objects.get(id=msg_id)
        message.is_read = True
        message.save()
        return Response({'status': 'success', 'message': 'Message marked as read'})
    except Message.DoesNotExist:
        return Response({'status': 'error', 'message': 'Message not found'}, status=status.HTTP_404_NOT_FOUND)
@api_view(['GET'])
def get_unread_messages(request, user_id):
    """
    Get all unread messages for the specified user.
    """
    unread_messages = Message.objects.filter(receiver_id=str(user_id), is_read=False).order_by('-created_at')
    serializer = MessageSerializer(unread_messages, many=True)
    return Response({'unread_messages': serializer.data})
@api_view(['GET'])
def get_user_chatrooms(request, user_id):
    """
    Return all chatrooms where the user is a member (sender or receiver).
    """
    chatrooms = ChatRoom.objects.filter(members__contains=[str(user_id)])
    serialized_chatrooms = [{'id': room.id, 'members': room.members} for room in chatrooms]
    return Response({'chatrooms': serialized_chatrooms})
