import dis
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core import serializers
from api.models import Book, Genre

CustomUser = get_user_model()

##########################################################################################
#                                         Books                                          #
##########################################################################################
def search(request):
  query = request.GET.get('q', '')
  sort_option = request.GET.get('sort', 'popularity')
  direction = request.GET.get('direction', 'desc')
  genre_slug = request.GET.get('genre', '')

  if not query.strip():
    results = Book.objects.all()
  else:
    results = Book.objects.filter(title__icontains=query)

  if genre_slug:
    results = results.filter(genre__name__icontains=genre_slug)

  order_prefix = '' if direction == 'asc' else '-'

  if sort_option == "rating":
    results = results.order_by(order_prefix + 'average_score')
  elif sort_option == "popularity":
    results = results.order_by(order_prefix + 'reviewers')
  elif sort_option == "newest":
    results = results.order_by(order_prefix + 'published_at')

  data = [{
    'model': 'api.book',
    'pk': book.id,
    'fields': {
        'id': book.id,
        'title': book.title,
        'author': book.author,
        'img_src': book.img_src,
        'genre': [genre.name for genre in book.genre.all()],
        'synopsis': book.synopsis.replace('|', '\n'),
        'reviewers': book.reviewers,
        'chapters': book.chapters,
        'score': book.score,
        'average_score': book.average_score,
        'published_at': book.published_at.strftime('%Y-%m-%d'),
    }
  } for book in results]
  return JsonResponse(data, safe=False)

def show_json_by_id(request, id):
    data = Book.objects.filter(pk=id)
    return HttpResponse(serializers.serialize("json", data), content_type="application/json")

def get_genres(request):
   genres = Genre.objects.all().order_by('name')
   genre_names = [genre.name for genre in genres]
   return JsonResponse(genre_names, safe=False)

def get_user(request):
    return JsonResponse({
        "display_name": request.user.display_name,
    }, status=200)

@csrf_exempt
def change_password(request):
    user = request.user
    old_password = request.POST['old_password']
    new_password = request.POST['new_password']
    display_name = request.POST['display_name']

    if not user.check_password(old_password):
        return JsonResponse({
            "status": False,
            "message": "Old password is incorrect."
        }, status=400)

    user.display_name = display_name
    user.set_password(new_password)
    user.save()

    return JsonResponse({
        "status": True,
        "message": "Password successfully changed."
    }, status=200)

##########################################################################################
#                                     Authentication                                     #
##########################################################################################

@csrf_exempt
def logout(request):
    auth_logout(request)
    return JsonResponse({
      "status": True,
      "message": "Successfully Logged Out!"
    }, status=200)

@csrf_exempt
def login(request):
    username = request.POST['username']
    password = request.POST['password']
    user = authenticate(username=username, password=password)
    if user is not None:
        if user.is_active:
            auth_login(request, user, backend='api.backend.CustomBackend')
            return JsonResponse({
              "status": True,
              "message": "Successfully Logged In!"
            }, status=200)
        else:
            return JsonResponse({
              "status": False,
              "message": "Failed to Login, Account Disabled."
            }, status=401)

    else:
        return JsonResponse({
          "status": False,
          "message": "Failed to Login, check your email/password."
        }, status=401)

@csrf_exempt
def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Basic validation
        if not username or not password:
            return JsonResponse({
                "status": False,
                "message": "Username, password, and email are required."
            }, status=400)

        # Check if user already exists
        if CustomUser.objects.filter(username=username).exists():
            return JsonResponse({
                "status": False,
                "message": "Username already exists."
            }, status=400)

        # Create the user
        try:
            user = CustomUser.objects.create(
                display_name=username,
                username=username,
                password=make_password(password),
            )
            user.is_active = True
            user.save()

            return JsonResponse({
                "status": True,
                "message": "User successfully registered."
            }, status=201)

        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": f"Error occurred during registration: {str(e)}"
            }, status=500)
    else:
        return JsonResponse({
            "status": False,
            "message": "Invalid request method."
        }, status=400)
