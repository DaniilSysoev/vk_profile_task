from django.db import models
from django.contrib.auth import get_user_model


class FriendsList(models.Model):
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE, related_name='user_id')
    friends = models.ManyToManyField(get_user_model(), blank=True, related_name='friends')

    def __str__(self):
        return self.user.username
    
    class Meta:
        verbose_name = 'Список друзей'
        verbose_name_plural = 'Списки друзей'


class Requests(models.Model):
    sender_id = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='sender')
    receiver_id = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='receiver')

    def __str__(self):
        return f'{self.sender_id.username} отправил заявку {self.receiver_id.username}'
    
    class Meta:
        verbose_name = 'Заявка'
        verbose_name_plural = 'Заявки'