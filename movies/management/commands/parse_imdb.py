import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
from django.core.management.base import BaseCommand
from movies.models import Movie, Director, Actor, Tag


class Command(BaseCommand):
    help = 'Parse top movies from IMDb'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=10, help='Number of movies to parse')
        parser.add_argument('--delay', type=float, default=2.0, help='Delay between requests')

    def get_page(self, url):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.text
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Request failed: {e}'))
            return None

    def parse_top_movies(self, count):
        url = "https://www.imdb.com/chart/top/"
        html = self.get_page(url)
        if not html:
            return []

        soup = BeautifulSoup(html, 'html.parser')
        movies = []

        for item in soup.select('li.ipc-metadata-list-summary-item')[:count]:
            try:
                title = item.select_one('h3.ipc-title__text').text.split('. ')[1]
                year = int(item.select('span.cli-title-metadata-item')[0].text)
                rating_text = item.select_one('span.ipc-rating-star').text.split()[0]
                rating = float(rating_text.split('(')[0])
                movie_url = "https://www.imdb.com" + item.select_one('a.ipc-title-link-wrapper')['href'].split('?')[0]

                movies.append({
                    'title': title,
                    'year': year,
                    'rating': rating,
                    'url': movie_url
                })
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Skipping movie: {e}'))

        return movies

    def parse_movie_details(self, url):
        html = self.get_page(url)
        if not html:
            return {}

        soup = BeautifulSoup(html, 'html.parser')
        details = {}

        try:
            # Описание
            details['description'] = soup.select_one('span.sc-16ede01-0').text if soup.select_one(
                'span.sc-16ede01-0') else ""

            # Жанры
            genres = [g.text for g in soup.select('a.ipc-chip--on-baseAlt')]
            details['genres'] = genres[:3]  # Берем первые 3 жанра

            # Режиссер
            director_section = soup.find('div', {'data-testid': 'title-pc-wide-screen'})
            if director_section:
                director_label = director_section.find('span', string='Director') or director_section.find('span',
                                                                                                           string='Directors')
                if director_label:
                    details['director'] = director_label.find_next('a').text

            # Актеры
            actors = []
            actor_blocks = soup.select('a[data-testid="title-cast-item__actor"]')[:5]
            for actor in actor_blocks:
                actors.append(actor.text)
            details['actors'] = actors

            # Постер
            details['poster_url'] = soup.select_one('img.ipc-image')['src'] if soup.select_one('img.ipc-image') else ""

        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Error parsing details: {e}'))

        return details

    def handle(self, *args, **options):
        count = options['count']
        delay = options['delay']

        self.stdout.write(self.style.SUCCESS(f'Starting parser for {count} movies...'))

        movies = self.parse_top_movies(count)
        if not movies:
            self.stdout.write(self.style.ERROR('No movies found'))
            return

        for i, movie_data in enumerate(movies, 1):
            self.stdout.write(f"\nProcessing {i}/{len(movies)}: {movie_data['title']}")

            details = self.parse_movie_details(movie_data['url'])
            if not details:
                continue

            try:
                # Создаем объект фильма
                movie, created = Movie.objects.get_or_create(
                    title=movie_data['title'],
                    release_date=datetime(movie_data['year'], 1, 1),
                    defaults={
                        'rating': movie_data['rating'],
                        'description': details.get('description', ''),
                        'poster_url': details.get('poster_url', '')  # Пока закомментируйте
                    }
                )

                # Добавляем режиссера
                if 'director' in details:
                    director, _ = Director.objects.get_or_create(name=details['director'])
                    movie.director = director

                # Добавляем актеров
                for actor_name in details.get('actors', [])[:5]:
                    actor, _ = Actor.objects.get_or_create(name=actor_name)
                    movie.actors.add(actor)

                # Добавляем теги (жанры)
                for genre in details.get('genres', [])[:3]:
                    tag, _ = Tag.objects.get_or_create(name=genre)
                    movie.tags.add(tag)

                movie.save()

                if created:
                    self.stdout.write(self.style.SUCCESS('Created'))
                else:
                    self.stdout.write(self.style.WARNING('Already exists'))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error saving: {e}'))

            time.sleep(delay)

        self.stdout.write(self.style.SUCCESS('\nDone!'))