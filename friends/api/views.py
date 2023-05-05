from rest_framework import viewsets, permissions
from django.contrib.auth import get_user_model
from rest_framework import generics
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from .models import FriendsList, Requests
from .serializers import FriendSerializer, RequestsSerializer, UserSerializer
from rest_framework.decorators import action



class UserViewSet(viewsets.ModelViewSet):
    queryset = get_user_model().objects.all()
    serializer_class = UserSerializer
    permission_classes = (permissions.AllowAny,)

    #создать пользователя и получить токен
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            FriendsList.objects.create(user=user)
            token = Token.objects.create(user=user)
            return Response({'token': token.key}, status=201)
        return Response(serializer.errors, status=400)
    
    #получить всех пользователей
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = UserSerializer(queryset, many=True)
        return Response(serializer.data)
    
    #логин и получение токена
    @action(methods=['post'], detail=False)
    def login(self, request, *args, **kwargs):
        data = request.data
        password = data.get('password', None)
        username = data.get('username', None)
        user = self.get_queryset().get(username=username, password=password)
        if user:
            token = Token.objects.get(user=user)
            return Response({'token': token.key}, status=200)
        return Response({'error': 'Wrong Credentials'}, status=400)
    
    #отправить заявку в друзья
    @action(methods=['post'], detail=True, url_path='add_friend')
    def add_friend(self, request, pk=None, *args, **kwargs):
        data = request.data
        data['sender_id'] = request.user.id
        data['receiver_id'] = pk
        serializer = RequestsSerializer(data=data)
        if serializer.is_valid():
            if int(pk) == data['sender_id']:
                return Response({'error': 'Вы не можете отправить заявку сами себе'}, status=400)
            if Requests.objects.filter(sender_id=data['sender_id'], receiver_id=pk).exists():
                return Response({'error': 'Такая заявка уже существует'}, status=400)
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


class RequestsViewSet(viewsets.ModelViewSet):
    queryset = Requests.objects.all()
    serializer_class = RequestsSerializer
    permission_classes = (permissions.IsAuthenticated,)

    #создать заявку
    def create(self, request, *args, **kwargs):
        data = request.data
        data['sender_id'] = request.user.id
        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            if data['sender_id'] == data['receiver_id']:
                return Response({'error': 'Вы не можете отправить заявку сами себе'}, status=400)
            if Requests.objects.filter(sender_id=data['sender_id'], receiver_id=data['receiver_id']).exists():
                return Response({'error': 'Такая заявка уже существует'}, status=400)
            if FriendsList.objects.get(user=data['sender_id']).friends.filter(id=data['receiver_id']).exists() or FriendsList.objects.get(user=data['receiver_id']).friends.filter(id=data['sender_id']).exists():
                return Response({'error': 'Вы уже друзья'}, status=400)
            #если такая заявка существует от другого пользователя, то принять её
            if Requests.objects.filter(sender_id=data['receiver_id'], receiver_id=data['sender_id']).exists():
                instance = Requests.objects.get(sender_id=data['receiver_id'], receiver_id=data['sender_id'])
                user1 = FriendsList.objects.get(user=instance.sender_id)
                user1.friends.add(instance.receiver_id)
                user1.save()
                user2 = FriendsList.objects.get(user=instance.receiver_id)
                user2.friends.add(instance.sender_id)
                user2.save()
                instance.delete()
                return Response({'message': 'Заявка принята'}, status=201)
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)
    
    #удалить\отклонить заявку
    def destroy(self, request, pk=None, *args, **kwargs):
        queryset = self.get_queryset()
        instance = queryset.get(id=pk)
        if instance.sender_id == request.user or instance.receiver_id == request.user:
            instance.delete()
            return Response({'message': 'Заявка удалена'}, status=204)
        return Response({'error': 'Вы не можете удалить эту заявку'}, status=400)

    #посмотреть исходящие заявки
    @action(methods=['get'], detail=False)
    def sended(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        sended = queryset.filter(sender_id=request.user.id)
        serializer = self.get_serializer(sended, many=True)
        return Response(serializer.data)
    
    #посмотреть входящие заявки
    @action(methods=['get'], detail=False)
    def received(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        received = queryset.filter(receiver_id=request.user.id)
        serializer = self.get_serializer(received, many=True)
        return Response(serializer.data)
    
    #принять заявку
    @action(methods=['post'], detail=True, url_path='accept')
    def accept(self, request, pk=None, *args, **kwargs):
        queryset = self.get_queryset()
        instance = queryset.get(id=pk)
        if instance.receiver_id == request.user:
            user1 = FriendsList.objects.get(user=instance.sender_id)
            user1.friends.add(instance.receiver_id)
            user1.save()
            user2 = FriendsList.objects.get(user=instance.receiver_id)
            user2.friends.add(instance.sender_id)
            user2.save()
            instance.delete()
            return Response({'message': 'Заявка принята'}, status=201)
        return Response({'error': 'Вы не можете принять эту заявку'}, status=400)
    
    #доступ к list только у юзеров с is_staff=True
    def list(self, request, *args, **kwargs):
        if request.user.is_staff:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        return Response({'error': 'У вас нет доступа к этому разделу'}, status=400)