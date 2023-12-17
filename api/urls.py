from django.urls import path, include
from api.views import (
    register, 
    login, 
    show_json_by_id, 
    search,
    get_genres,
    )

app_name = 'api'

urlpatterns = [
    path('login/', login),
    path('register/', register),
    path('json/<int:id>/', show_json_by_id),
    path('search/', search),
    path('get_genres/', get_genres),
]