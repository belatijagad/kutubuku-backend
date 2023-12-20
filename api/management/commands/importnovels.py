from django.core.management.base import BaseCommand
import json
from api.models import Book, Genre

class Command(BaseCommand):
    help = 'Imports novels from a JSON file into the database'

    def handle(self, *args, **options):
        with open('utils/output/novels_cleaned.json', 'r', encoding='utf-8') as file:
            data = json.load(file)

        for novel_data in data:
            novel = Book()
            novel.title = novel_data['title']
            novel.author = novel_data['author']
            novel.chapters = novel_data['chapters']
            novel.img_src = novel_data['img_src']
            novel.synopsis = novel_data['synopsis']
            novel.reviewers = novel_data['reviewers']
            novel.score = novel_data['score'] * novel_data['reviewers'] if novel_data['reviewers'] else 0
            novel.average_score = novel_data['score']
            novel.is_approved = True
            novel.save()

            for genre in novel_data['genres']:
                genre, created = Genre.objects.get_or_create(name=genre.strip())
                novel.genre.add(genre)

        self.stdout.write(self.style.SUCCESS('Successfully imported novels'))