import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
from django.core.management.base import BaseCommand
from movies.models import Movie, Director, Actor, Tag


class Command(BaseCommand):
    """Команда для парсинга топовых фильмов с IMDb и сохранения в базу данных"""
    help = 'Parse top movies from IMDb'

    def add_arguments(self, parser):
        """Добавляем кастомные аргументы команды"""
        parser.add_argument(
            '--count',
            type=int,
            default=10,
            help='Сколько фильмов парсить (по умолчанию 10)'
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=2.0,
            help='Задержка между запросами в секундах (чтобы не забанили)'
        )

    def get_page(self, url):
        """
        Выполняет HTTP-запрос к указанному URL
        Возвращает HTML-страницу или None при ошибке
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()  # Проверяем статус ответа
            return response.text
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ошибка запроса: {e}'))
            return None

    def parse_top_movies(self, count):
        """
        Парсит список топ-N фильмов с главной страницы IMDb
        Возвращает список словарей с базовой информацией о фильмах
        """
        url = "https://www.imdb.com/chart/top/"
        html = self.get_page(url)
        if not html:
            return []

        soup = BeautifulSoup(html, 'html.parser')
        movies = []

        # Ищем все элементы с фильмами в таблице
        for item in soup.select('li.ipc-metadata-list-summary-item')[:count]:
            try:
                # Извлекаем номер, название и год (формат: "1. Название (2023)")
                raw_title = item.select_one('h3.ipc-title__text').text
                title = raw_title.split('. ')[1]  # Убираем номер из начала

                # Год выпуска (первый элемент в metadata)
                year = int(item.select('span.cli-title-metadata-item')[0].text)

                # Рейтинг (формат: "8.7 (1.2M)")
                rating_text = item.select_one('span.ipc-rating-star').text
                rating = float(rating_text.split()[0])  # Берем только число

                # Ссылка на страницу фильма
                movie_url = "https://www.imdb.com" + item.select_one('a.ipc-title-link-wrapper')['href'].split('?')[0]

                movies.append({
                    'title': title,
                    'year': year,
                    'rating': rating,
                    'url': movie_url
                })
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Пропускаем фильм из-за ошибки: {e}'))

        return movies

    def parse_movie_details(self, url):
        """
        Парсит детальную информацию о фильме со страницы
        Возвращает словарь с доп. данными (описание, жанры, актеры)
        """
        html = self.get_page(url)
        if not html:
            return {}

        soup = BeautifulSoup(html, 'html.parser')
        details = {}

        try:
            # Описание фильма
            desc_tag = soup.select_one('span.sc-16ede01-0')
            details['description'] = desc_tag.text if desc_tag else "Нет описания"

            # Жанры (первые 3)
            genres = [g.text for g in soup.select('a.ipc-chip--on-baseAlt')]
            details['genres'] = genres[:3] if genres else ['Unknown']

            # Режиссер (может быть несколько, берем первого)
            director_section = soup.find('div', {'data-testid': 'title-pc-wide-screen'})
            if director_section:
                director_label = director_section.find('span', string='Director') or \
                                 director_section.find('span', string='Directors')
                if director_label:
                    details['director'] = director_label.find_next('a').text

            # Актеры (первые 5 в списке)
            actors = []
            actor_blocks = soup.select('a[data-testid="title-cast-item__actor"]')[:5]
            for actor in actor_blocks:
                actors.append(actor.text)
            details['actors'] = actors if actors else ['Unknown']

            # Ссылка на постер
            poster_img = soup.select_one('img.ipc-image')
            details['poster_url'] = poster_img['src'] if poster_img else ""

        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Ошибка парсинга деталей: {e}'))

        return details

    def handle(self, *args, **options):
        """
        Основной метод, который выполняется при вызове команды
        Последовательность работы:
        1. Парсим список топовых фильмов
        2. Для каждого фильма парсим детали
        3. Сохраняем в базу данных
        """
        count = options['count']
        delay = options['delay']

        self.stdout.write(self.style.SUCCESS(f'Начинаем парсинг {count} фильмов...'))

        # Получаем список топовых фильмов
        movies = self.parse_top_movies(count)
        if not movies:
            self.stdout.write(self.style.ERROR('Не найдено ни одного фильма'))
            return

        # Обрабатываем каждый фильм
        for i, movie_data in enumerate(movies, 1):
            self.stdout.write(f"\nОбрабатываем {i}/{len(movies)}: {movie_data['title']}")

            # Парсим детальную информацию
            details = self.parse_movie_details(movie_data['url'])
            if not details:
                continue

            try:
                # Создаем или обновляем фильм в базе
                movie, created = Movie.objects.get_or_create(
                    title=movie_data['title'],
                    release_date=datetime(movie_data['year'], 1, 1),  # Дата без месяца/дня
                    defaults={
                        'rating': movie_data['rating'],
                        'description': details.get('description', ''),
                        'poster_url': details.get('poster_url', '')
                    }
                )

                # Добавляем режиссера (если нашли)
                if 'director' in details:
                    director, _ = Director.objects.get_or_create(name=details['director'])
                    movie.director = director

                # Добавляем актеров (не больше 5)
                for actor_name in details.get('actors', [])[:5]:
                    actor, _ = Actor.objects.get_or_create(name=actor_name)
                    movie.actors.add(actor)

                # Добавляем жанры (не больше 3)
                for genre in details.get('genres', [])[:3]:
                    tag, _ = Tag.objects.get_or_create(name=genre)
                    movie.tags.add(tag)

                movie.save()

                if created:
                    self.stdout.write(self.style.SUCCESS('Создан новый фильм'))
                else:
                    self.stdout.write(self.style.WARNING('Фильм уже существует'))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Ошибка сохранения: {e}'))

            # Делаем паузу между запросами
            time.sleep(delay)

        self.stdout.write(self.style.SUCCESS('\nГотово! Все фильмы обработаны'))