from django.db import models
from django.contrib.auth.models import AbstractUser, Group

class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Book(models.Model):
    # Kalau author empty, bakal pake user, dan sebaliknya.
    author = models.TextField(blank=True)
    user = models.ForeignKey('CustomUser', on_delete=models.SET_NULL, null=True, blank=True)
    is_approved = models.BooleanField(default=False)

    # Field yang bakal disediain di form
    title = models.TextField()
    chapters = models.IntegerField()
    img_src = models.TextField()
    genre = models.ManyToManyField(Genre)
    synopsis = models.TextField()

    # Bakal bertambah seiring ada reviewer, gak ada di form
    reviewers = models.IntegerField(default=0)
    score = models.FloatField(default=0)
    average_score = models.FloatField(default=0)

    # Secara otomatis terbuat ketika ngebikin object
    published_at = models.DateField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.author and self.user:
            self.author = str(self.user)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['published_at']

class CustomUser(AbstractUser):
    bookmarks = models.ManyToManyField(Book, blank=True)
    display_name = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.username

class Ulasan(models.Model):
    # Secara otomatis terbuat ketika ngebikin object
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)

    # Review dan isi review
    rating = models.IntegerField(null=True, blank=True)
    comment = models.TextField()

    # Bakal bertambah seiring ada upvote atau downvote
    upvotes = models.IntegerField(default=0)
    downvotes = models.IntegerField(default=0)

    # Secara otomatis terbuat ketika ngebikin object
    created_at = models.DateTimeField(auto_now_add=True)

class ReviewVote(models.Model):
    UPVOTE = 'U'
    DOWNVOTE = 'D'
    VOTE_TYPES = [
        (UPVOTE, 'Upvote'),
        (DOWNVOTE, 'Downvote'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    review = models.ForeignKey('Ulasan', on_delete=models.CASCADE, related_name='votes')
    vote_type = models.CharField(max_length=1, choices=VOTE_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'review')  # Ensure one vote per user per review


class ReadingProgress(models.Model):
    # Inisiasi secara otomatis
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    current_chapter = models.IntegerField(default=1)
    start_date = models.DateField(auto_now_add=True)
    last_read = models.DateField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s progress in {self.book.title}"

    class Meta:
        unique_together = ('user', 'book')
