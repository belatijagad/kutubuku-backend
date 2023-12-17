from django.urls import path
from api.views import (
    register,
    login,
    logout,
    change_password,
    show_json_by_id,
    search,
    get_genres,
    get_user,
    )

app_name = 'api'

urlpatterns = [
    path('login/', login),
    path('logout/', logout),
    path('register/', register),
    path('change_password/', change_password),
    path('json/<int:id>/', show_json_by_id),
    path('search/', search),
    path('get_genres/', get_genres),
    path('get_user/', get_user),
]