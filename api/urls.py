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
    toggle_bookmark,
    search_bookmark,
    is_bookmarked,
    submit_review,
    fetch_reviews,
    delete_review,
    get_user_review,
    update_or_create_progress,
    get_reading_progress,
    )

app_name = 'api'

urlpatterns = [
    path('login/', login),
    path('logout/', logout),
    path('register/', register),
    path('change_password/', change_password),
    path('json/<int:id>/', show_json_by_id),
    path('search/', search),
    path('search_bookmark/', search_bookmark),
    path('get_genres/', get_genres),
    path('get_user/', get_user),
    path('bookmark/<int:book_id>/', toggle_bookmark),
    path('is_bookmarked/<int:book_id>/', is_bookmarked),
    path('submit_review/<int:book_id>/', submit_review),
    path('fetch_reviews/<int:book_id>/', fetch_reviews),
    path('delete_review/<int:review_id>/', delete_review),
    path('get_review/<int:book_id>/', get_user_review),
    path('update_progress/<int:book_id>/<int:chapter_number>/', update_or_create_progress),
    path('get_progress/<int:book_id>/', get_reading_progress),
]