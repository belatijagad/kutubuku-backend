from django.urls import path, include
from api.views import (
    register, 
    login, 
    show_json_by_id, 
    search,
    get_genres,
    get_user_details,
    logout
    )

app_name = 'api'

urlpatterns = [
    path('login/', login),
    path('logout/', logout, name='logout'),
    path('register/', register),
    path('json/<int:id>/', show_json_by_id),
    path('search/', search),
    path('get_genres/', get_genres),
    path('user/<str:username>/', get_user_details),
]