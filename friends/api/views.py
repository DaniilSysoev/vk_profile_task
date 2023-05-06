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
    allowed_methods = ('POST', 'GET', 'HEAD', 'OPTIONS')

    #создать пользователя и получить токен
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            print(1)
            FriendsList.objects.create(user=user)
            print(2)
            token = Token.objects.create(user=user)
            print(3)
            return Response({'token': token.key}, status=201)
        return Response(serializer.errors, status=400)
    
    #получить всех пользователей или если авторизован всех кроме себя
    def list(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            queryset = self.get_queryset().exclude(id=request.user.id)
        else:
            queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=200)
    
    #получить детально пользователя и добавить поле о статусе дружбы (нет ничего, есть исходящая заявка, есть входящая заявка, уже друзья)
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = UserSerializer(instance)
        status = {"Пользователь": serializer.data, "Статус": "Ничего нет"}
        if FriendsList.objects.get(user=instance).friends.filter(id=request.user.id).exists():
            status['Статус'] = 'Вы уже друзья'
        elif Requests.objects.filter(sender_id=instance, receiver_id=request.user.id).exists():
            status['Статус'] = 'Вы отправили заявку'
        elif Requests.objects.filter(sender_id=request.user.id, receiver_id=instance).exists():
            status['Статус'] = 'Вам отправили заявку'
        elif instance.id == request.user.id:
            status['Статус'] = 'Это вы'
        return Response(status, status=200)
    
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
            if FriendsList.objects.get(user=data['sender_id']).friends.filter(id=pk).exists() or FriendsList.objects.get(user=pk).friends.filter(id=data['sender_id']).exists():
                return Response({'error': 'Вы уже друзья'}, status=400)
            #если такая заявка существует от другого пользователя, то принять её
            if Requests.objects.filter(sender_id=pk, receiver_id=data['sender_id']).exists():
                instance = Requests.objects.get(sender_id=pk, receiver_id=data['sender_id'])
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


class RequestsViewSet(viewsets.ModelViewSet):
    queryset = Requests.objects.all()
    serializer_class = RequestsSerializer
    permission_classes = (permissions.IsAuthenticated,)
    allowed_methods = ('POST', 'GET', 'HEAD', 'OPTIONS', 'DELETE')

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

    #посмотреть исходящие заявки
    @action(methods=['get'], detail=False)
    def sended(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        sended = queryset.filter(sender_id=request.user.id)
        serializer = self.get_serializer(sended, many=True)
        return Response(serializer.data, status=200)
    
    #посмотреть входящие заявки
    @action(methods=['get'], detail=False)
    def received(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        received = queryset.filter(receiver_id=request.user.id)
        serializer = self.get_serializer(received, many=True)
        return Response(serializer.data, status=200)
    
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
    
    #удалить\отклонить заявку
    @action(methods=['post'], detail=True, url_path='delete')
    def delete(self, request, pk=None, *args, **kwargs):
        queryset = self.get_queryset()
        instance = queryset.get(id=pk)
        if instance.sender_id == request.user or instance.receiver_id == request.user:
            instance.delete()
            return Response({'message': 'Заявка удалена'}, status=204)
        return Response({'error': 'Вы не можете удалить эту заявку'}, status=400)
    
    #доступ к list только у юзеров с is_staff=True
    def list(self, request, *args, **kwargs):
        if request.user.is_staff:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data, status=200)
        return Response({'error': 'У вас нет доступа к этому разделу'}, status=400)


class FriendsListViewSet(viewsets.ModelViewSet):
    queryset = FriendsList.objects.all()
    serializer_class = FriendSerializer
    permission_classes = (permissions.IsAuthenticated,)
    allowed_methods = ('GET', 'HEAD', 'OPTIONS', 'DELETE')

    #посмотреть список друзей
    def list(self, request, *args, **kwargs):
        friends = FriendsList.objects.get(user=request.user.id)
        serializer = self.get_serializer(friends)
        #возвращать username друзей
        for i in range(len(serializer.data['friends'])):
            serializer.data['friends'][i] = get_user_model().objects.get(id=serializer.data['friends'][i]).username
        return Response(serializer.data['friends'], status=200)
    
    #удалить друга и переместить его в список заявок
    def destroy(self, request, pk=None, *args, **kwargs):
        queryset = self.get_queryset()
        instance = queryset.get(user=request.user.id)
        if instance.friends.filter(id=pk).exists():
            #если друга не существует или его нет в списке друзей, то вернуть ошибку
            if not get_user_model().objects.filter(id=pk).exists() and not instance.friends.filter(id=pk).exists():
                return Response({'error': 'Такого друга нет'}, status=400)
            instance.friends.remove(pk)
            Requests.objects.create(sender_id=get_user_model().objects.get(id=pk), receiver_id=request.user)
            #удалить из друзей друга, которого удалили
            if FriendsList.objects.get(user=pk).friends.filter(id=request.user.id).exists():
                user = FriendsList.objects.get(user=pk)
                user.friends.remove(request.user.id)
                user.save()
            return Response({'message': 'Друг удалён'}, status=204)
        return Response({'error': 'Такого друга нет'}, status=400)
    
    #нет доступа к retrieve
    def retrieve(self, request, pk=None, *args, **kwargs):
        return Response({'error': 'Нет доступа к этому разделу'}, status=400)