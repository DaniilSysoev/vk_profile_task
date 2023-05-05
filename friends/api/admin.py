from django.contrib import admin
from .models import FriendsList, Requests


@admin.register(FriendsList)
class FriendsListAdmin(admin.ModelAdmin):
    list_display = ('user', )


@admin.register(Requests)
class RequestsAdmin(admin.ModelAdmin):
    list_display = ('sender_id', 'receiver_id')