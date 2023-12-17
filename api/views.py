from django.contrib.auth import authenticate, get_user_model, logout as auth_logout, login as auth_login
from django.contrib.auth.decorators import login_required
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

# @login_required(login_url='/api/login/')
def get_user_details(request, username):
    user = CustomUser.objects.get(username=username)
    return JsonResponse({'username': user.get_username()})

##########################################################################################
#                                     Authentication                                     #
##########################################################################################

@csrf_exempt
def login(request):
    username = request.POST['username']
    password = request.POST['password']
    user = authenticate(username=username, password=password)
    if user is not None:
        if user.is_active:
            auth_login(request, user)
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
def logout(request):
    username = request.user.username

    try:
        auth_logout(request)
        return JsonResponse({
            "username": username,
            "status": True,
            "message": "Logout berhasil!"
        }, status=200)
    except:
        return JsonResponse({
        "status": False,
        "message": "Logout gagal."
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
                username=username,
                password=make_password(password),
                # Set other CustomUser fields here if necessary
            )
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
