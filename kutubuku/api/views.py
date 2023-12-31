import json
import dis
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.core import serializers
from api.models import Book, Genre, ReadingProgress, ReviewVote, Ulasan
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_http_methods
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import F, ExpressionWrapper, IntegerField
from django.db.models.functions import Cast


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
    results = Book.objects.filter(is_approved=True)
  else:
    results = Book.objects.filter(is_approved=True, title__icontains=query)

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
        'synopsis': book.synopsis,
        'reviewers': book.reviewers,
        'chapters': book.chapters,
        'score': book.score,
        'average_score': book.average_score,
        'published_at': book.published_at.strftime('%Y-%m-%d'),
    }
  } for book in results]
  return JsonResponse(data, safe=False)

def fetch_approval(request):
    books = Book.objects.filter(is_approved=False)
    data = [{
    'model': 'api.book',
    'pk': book.id,
    'fields': {
        'id': book.id,
        'title': book.title,
        'author': book.author,
        'img_src': book.img_src,
        'genre': [genre.name for genre in book.genre.all()],
        'synopsis': book.synopsis,
        'reviewers': book.reviewers,
        'chapters': book.chapters,
        'score': book.score,
        'average_score': book.average_score,
        'published_at': book.published_at.strftime('%Y-%m-%d'),
    }} for book in books]
    return JsonResponse(data, safe=False)

def delete_book(request, book_id):
    try:
        book = Book.objects.get(pk=book_id)
        book.delete()
        return JsonResponse({'status': 'Success'})
    except e:
        return JsonResponse({'status': 'Failed'})
    
def approve_book(request, book_id):
    try:
        book = Book.objects.get(pk=book_id)
        book.is_approved = True
        book.save()
        print(book)
        return JsonResponse({'status': 'Success'})
    except e:
        return JsonResponse({'status': 'Failed'})

def show_json_by_id(request, id):
    data = Book.objects.filter(pk=id)
    return HttpResponse(serializers.serialize("json", data), content_type="application/json")

def get_genres(request):
   genres = Genre.objects.all().order_by('name')
   genre_names = [genre.name for genre in genres]
   return JsonResponse(genre_names, safe=False)

@login_required
@csrf_exempt
def add_book(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            title = data.get('title')
            chapters = data.get('chapters')
            img_src = data.get('img_src')
            synopsis = data.get('synopsis')
            genre_names = data.get('genre')

            # Validate required fields
            if not title or not chapters or not img_src or not synopsis:
                return JsonResponse({'status': 'error', 'message': 'Missing required fields.'}, status=400)

            # Create the book instance
            book = Book(
                title=title,
                chapters=chapters,
                img_src=img_src,
                synopsis=synopsis,
                user=request.user if not request.user.is_anonymous else None
            )
            book.save()

            # Add genres to the book
            for name in genre_names.split(','):
                name = name.title()
                genre, created = Genre.objects.get_or_create(name=name)
                book.genre.add(genre)

            book.save()

            return JsonResponse({'status': 'success', 'message': 'Book added successfully.', 'book_id': book.id}, status=201)

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=400)


##########################################################################################
#                                         User                                           #
##########################################################################################

def get_user(request):
    return JsonResponse({
        "username": request.user.username,
        "is_superuser": request.user.is_superuser,
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
#                                      Bookmarks                                         #
##########################################################################################

@login_required
@csrf_exempt
def toggle_bookmark(request, book_id):
    user = request.user
    try:
        book = Book.objects.get(id=book_id)
        if book in user.bookmarks.all():
            user.bookmarks.remove(book)
            is_bookmarked = False
        else:
            user.bookmarks.add(book)
            is_bookmarked = True
        return JsonResponse({'bookmarked': is_bookmarked, 'statusCode': 200}, status=200)
    except Book.DoesNotExist:
        return JsonResponse({'error': 'Book not found'}, status=404)
    
@login_required
def search_bookmark(request):
    query = request.GET.get('q', '')
    sort_option = request.GET.get('sort', 'popularity')
    direction = request.GET.get('direction', 'desc')
    genre_slug = request.GET.get('genre', '')

    # Get the currently logged-in user
    user = request.user

    # Filter the books that are bookmarked by the user
    results = user.bookmarks.all()

    if query.strip():
        results = results.filter(title__icontains=query)

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
            'synopsis': book.synopsis,
            'reviewers': book.reviewers,
            'chapters': book.chapters,
            'score': book.score,
            'average_score': book.average_score,
            'published_at': book.published_at.strftime('%Y-%m-%d'),
        }
    } for book in results]

    return JsonResponse(data, safe=False)

@login_required
def is_bookmarked(request, book_id):
    try:
        book = Book.objects.get(id=book_id)
        is_bookmarked = book in request.user.bookmarks.all()
        return JsonResponse({'is_bookmarked': is_bookmarked})
    except Book.DoesNotExist:
        return JsonResponse({'error': 'Book not found'}, status=404)
    
@login_required
def update_or_create_progress(request, book_id, chapter_number):
    book = get_object_or_404(Book, pk=book_id)
    user = request.user

    progress, created = ReadingProgress.objects.get_or_create(
        user=user,
        book=book,
        defaults={'current_chapter': chapter_number}
    )
    
    if not created and chapter_number > progress.current_chapter:
        progress.current_chapter = chapter_number
        progress.save(update_fields=['current_chapter', 'last_read'])

    return JsonResponse({
        'status': 'updated' if not created else 'created',
        'current_chapter': progress.current_chapter,
        'statusCode': 200,
    })

@login_required
def get_reading_progress(request, book_id):
    user = request.user
    try:
        reading_progress = ReadingProgress.objects.get(user=user, book_id=book_id)
        data = {
            'current_chapter': reading_progress.current_chapter,
            'total_chapters': reading_progress.book.chapters,
            'statusCode': 200,
            'last_read': reading_progress.last_read,
        }
        return JsonResponse(data, status=200)
    except ReadingProgress.DoesNotExist:
        return JsonResponse({'current_chapter': 0, 'statusCode': 200}, status=404)
    except Exception as e:  
        return JsonResponse({'error': str(e), 'statusCode': 400}, status=500)


##########################################################################################
#                                         Review                                         #
##########################################################################################

@require_POST
@csrf_exempt
@login_required
def submit_review(request, book_id):
    try:
        user = request.user
        book = Book.objects.get(id=book_id)
        data = json.loads(request.body)

        rating = data.get('rating')
        comment = data.get('comment')

        # Validate data
        if not rating or not comment:
            return JsonResponse({'status': 'error', 'message': 'Rating and comment are required.'}, status=400)

        # Create and save the review
        review = Ulasan(user=user, book=book, rating=rating, comment=comment)
        review.save()

        book.reviewers += 1
        book.score += rating * 20
        book.average_score = 0 if not book.reviewers else book.score / book.reviewers
        book.save()

        return JsonResponse({'statusCode': 201, 'message': 'Review submitted successfully.'}, status=201)

    except Book.DoesNotExist:
        return JsonResponse({'statusCode': 400, 'message': 'Book not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'statusCode': 400, 'message': str(e)}, status=500)
    

def fetch_reviews(request, book_id):
    try:
        book = Book.objects.get(id=book_id)
        reviews = Ulasan.objects.filter(book=book) \
            .annotate(vote_difference=ExpressionWrapper(F('upvotes') - F('downvotes'), output_field=IntegerField())) \
            .order_by('-vote_difference')

        reviews_data = [{
            'user': review.user.username,
            'id': review.pk,
            'rating': review.rating,
            'comment': review.comment,
            'upvotes': review.upvotes,
            'downvotes': review.downvotes,
            'created_at': review.created_at.strftime('%Y/%m/%d')
        } for review in reviews]

        return JsonResponse({'status': 'success', 'reviews': reviews_data}, safe=False)

    except ObjectDoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Book not found.'}, status=404)

@login_required
def delete_review(request, review_id):
    try:
        review = Ulasan.objects.get(pk=review_id)
        book = Book.objects.get(id=review.book.pk)

        book.reviewers += 1
        book.score -= review.rating * 20
        book.average_score = 0 if not book.reviewers else book.score / book.reviewers

        review.delete()
        book.save()

        return JsonResponse({'statusCode': 200, 'message': 'Review deleted successfully.'}, status=200)
    except Ulasan.DoesNotExist:
        return JsonResponse({'statusCode': 400, 'message': 'Review not found or not authorized to delete.'}, status=404)
    
@login_required
def get_user_review(request, book_id):
    user = request.user
    try:
        book = Book.objects.get(id=book_id)
        review = Ulasan.objects.get(book=book, user=user)
        review_data = {
            'id': review.id,
            'rating': review.rating,
            'comment': review.comment,
            'upvotes': review.upvotes,
            'downvotes': review.downvotes,
            'created_at': review.created_at.strftime('%Y/%m/%d'),
        }
        return JsonResponse({'status': 'success', 'review': review_data})
    except ObjectDoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Review not found.'}, status=404)

@login_required
def upvote_review(request, review_id):
    if request.user.is_authenticated:
        review = Ulasan.objects.get(pk=review_id)
        vote, created = ReviewVote.objects.get_or_create(user=request.user, review=review)

        if created or vote.vote_type == ReviewVote.DOWNVOTE:
            vote.vote_type = ReviewVote.UPVOTE
            vote.save()
            review.upvotes += 1
            if not created:
                review.downvotes -= 1  # Remove downvote if it existed
            review.save()
            return JsonResponse({'status': 'success', 'message': 'Review upvoted.'})
        else:
            return JsonResponse({'status': 'error', 'message': 'You have already upvoted this review.'})

    return JsonResponse({'status': 'error', 'message': 'You must be logged in to vote.'}, status=401)

@login_required
def downvote_review(request, review_id):
    if request.user.is_authenticated:
        review = Ulasan.objects.get(pk=review_id)
        vote, created = ReviewVote.objects.get_or_create(user=request.user, review=review)

        if created or vote.vote_type == ReviewVote.UPVOTE:
            vote.vote_type = ReviewVote.DOWNVOTE
            vote.save()
            review.downvotes += 1
            if not created:
                review.upvotes -= 1  # Remove upvote if it existed
            review.save()
            return JsonResponse({'status': 'success', 'message': 'Review downvoted.'})
        else:
            return JsonResponse({'status': 'error', 'message': 'You have already downvoted this review.'})

    return JsonResponse({'status': 'error', 'message': 'You must be logged in to vote.'}, status=401)

@login_required
def get_vote_status(request, review_id):
    try:
        review = Ulasan.objects.get(pk=review_id)
        vote = ReviewVote.objects.filter(user=request.user, review=review).first()

        if vote.vote_type == ReviewVote.UPVOTE:
            return JsonResponse({'voteStatus': 'upvote', 'status': 'success'})
        else:
            return JsonResponse({'voteStatus': 'downvote', 'status': 'success'})
    except ReviewVote.DoesNotExist:
        return JsonResponse({'message': 'Review not found.', 'status': 'error'}, status=404)
    except Exception as e:
        return JsonResponse({'message': str(e), 'status': 'error'}, status=500)


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
