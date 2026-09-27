"""
Кастомная команда Django: экспорт данных из БД в статические JSON-файлы
для полностью оффлайн-работы фронтенда (PWA).

Использование:
    python manage.py export_data

Результат: static/data/categories.json, templates.json, articles.json
"""

import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from core.models import Category, PromptTemplate, GuideArticle


class Command(BaseCommand):
    help = 'Экспортирует активные категории, шаблоны промптов и статьи в static/data/*.json'

    def add_arguments(self, parser):
        parser.add_argument(
            '--pretty',
            action='store_true',
            help='Форматированный вывод JSON (с отступами)',
        )

    def handle(self, *args, **options):
        out_dir = Path(settings.BASE_DIR) / 'static' / 'data'
        out_dir.mkdir(parents=True, exist_ok=True)

        indent = 2 if options.get('pretty') else None

        categories = list(
            Category.objects.filter(is_active=True)
            .order_by('order', 'name')
            .values('id', 'name', 'slug', 'description', 'icon', 'order')
        )

        templates = []
        for tpl in (
            PromptTemplate.objects
            .filter(is_active=True, category__is_active=True)
            .select_related('category')
            .order_by('category__order', 'name')
        ):
            templates.append({
                'id': tpl.id,
                'name': tpl.name,
                'category': tpl.category.name,
                'category__slug': tpl.category.slug,
                'system_prompt': tpl.system_prompt,
                'user_prompt_template': tpl.user_prompt_template,
                'variables': tpl.variables if isinstance(tpl.variables, list) else [],
            })

        articles = list(
            GuideArticle.objects.filter(is_published=True)
            .order_by('-published_at')
            .values('id', 'title', 'slug', 'excerpt', 'content',
                    'category', 'author', 'views')
        )

        files = {
            'categories.json': categories,
            'templates.json': templates,
            'articles.json': articles,
        }

        for filename, data in files.items():
            path = out_dir / filename
            with path.open('w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=indent)
            self.stdout.write(self.style.SUCCESS(
                f'✔ {path.relative_to(settings.BASE_DIR)} — записей: {len(data)}'
            ))

        self.stdout.write(self.style.SUCCESS(
            '\nЭкспорт завершён. Данные готовы для оффлайн-режима (Service Worker).'
        ))
