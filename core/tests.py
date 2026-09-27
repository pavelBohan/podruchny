"""
Тесты ядра приложения «Подручный»: модели, генерация промптов,
экспорт данных для оффлайн-режима и API конструктора.

Запуск:  python manage.py test core
"""

import json

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from core.models import Category, GeneratedPrompt, GuideArticle, PromptTemplate


class PromptTemplateGenerationTests(TestCase):
    """Проверка серверной генерации промпта из шаблона."""

    def setUp(self):
        self.category = Category.objects.create(
            name='План урока', slug='lesson_plan', order=1
        )
        self.template = PromptTemplate.objects.create(
            category=self.category,
            name='Классический план',
            system_prompt='Ты — методист.',
            user_prompt_template=(
                'Составь план урока: {subject}, {grade} класс, тема «{topic}». '
                'Тон: {tone}. Контекст: {additional_context}'
            ),
        )

    def test_generate_prompt_substitutes_all_placeholders(self):
        prompt = self.template.generate_prompt({
            'subject': 'Математика',
            'grade': '5',
            'topic': 'Дроби',
            'tone': 'professional',
            'additional_context': 'Класс слабый',
        })
        self.assertIn('Математика', prompt)
        self.assertIn('Дроби', prompt)
        self.assertIn('Ты — методист.', prompt)  # системный промпт в начале
        self.assertNotIn('{subject}', prompt)
        self.assertNotIn('{topic}', prompt)

    def test_generate_prompt_starts_with_system_prompt(self):
        prompt = self.template.generate_prompt({'subject': 'X', 'grade': '5', 'topic': 'Y'})
        self.assertTrue(prompt.startswith('Ты — методист.'))


class GenerateApiTests(TestCase):
    """Проверка эндпоинта /constructor/generate/ (серверная часть оффлайна)."""

    def setUp(self):
        self.category = Category.objects.create(name='Тесты', slug='test', order=2)
        self.template = PromptTemplate.objects.create(
            category=self.category,
            name='Тест на 10 вопросов',
            system_prompt='Ты — составитель тестов.',
            user_prompt_template='Сделай тест: {subject}, {grade} класс, {topic}',
        )
        self.url = reverse('core:generate_prompt')

    def _post(self, payload):
        return self.client.post(self.url, data=json.dumps(payload),
                                content_type='application/json')

    def test_success_returns_prompt_and_qwen_url(self):
        resp = self._post({
            'category': 'test',
            'context': {'subject': 'История', 'grade': '7', 'topic': 'Древняя Русь'},
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['success'])
        self.assertIn('История', data['prompt'])
        self.assertIn('chat.qwen.ai', data['qwen_url'])

    def test_missing_required_fields_returns_400(self):
        resp = self._post({'category': 'test', 'context': {'subject': '', 'grade': '7'}})
        self.assertEqual(resp.status_code, 400)
        self.assertIn('error', resp.json())

    def test_invalid_tone_falls_back_to_professional(self):
        resp = self._post({
            'category': 'test',
            'context': {'subject': 'Х', 'grade': '5', 'topic': 'Y', 'tone': 'hack'},
        })
        self.assertEqual(resp.status_code, 200)

    def test_long_context_truncated_to_500(self):
        long_ctx = 'A' * 1000
        resp = self._post({
            'category': 'test',
            'context': {'subject': 'Х', 'grade': '5', 'topic': 'Y',
                        'additional_context': long_ctx},
        })
        self.assertEqual(resp.status_code, 200)
        # Обрезанный контекст не должен встречаться в промпте целиком
        self.assertNotIn(long_ctx, resp.json()['prompt'])

    def test_unknown_category_returns_404(self):
        resp = self._post({
            'category': 'nope',
            'context': {'subject': 'Х', 'grade': '5', 'topic': 'Y'},
        })
        self.assertEqual(resp.status_code, 404)

    def test_history_saved_for_authenticated_user(self):
        user = User.objects.create_user('teacher', password='pass12345')
        self.client.force_login(user)
        self._post({
            'category': 'test',
            'context': {'subject': 'Биология', 'grade': '6', 'topic': 'Клетка'},
        })
        self.assertEqual(GeneratedPrompt.objects.filter(user=user).count(), 1)


class ExportDataCommandTests(TestCase):
    """Команда export_data должна писать JSON для оффлайн-режима."""

    def test_export_creates_json_files(self):
        category = Category.objects.create(name='Внеурочка', slug='extracurricular')
        PromptTemplate.objects.create(
            category=category, name='Классный час',
            system_prompt='Система', user_prompt_template='Тема: {topic}',
        )
        GuideArticle.objects.create(
            title='Статья', slug='article', excerpt='...', content='...',
            category='basics',
        )
        call_command('export_data')

        import os
        from django.conf import settings
        base = os.path.join(settings.BASE_DIR, 'static', 'data')
        for fname in ('categories.json', 'templates.json', 'articles.json'):
            path = os.path.join(base, fname)
            self.assertTrue(os.path.exists(path))
            with open(path, encoding='utf-8') as f:
                data = json.load(f)
            self.assertIsInstance(data, list)


class PageSmokeTests(TestCase):
    """Все ключевые страницы отдают 200 (в т.ч. для кэша Service Worker)."""

    def test_pages_available(self):
        Category.objects.create(name='План урока', slug='lesson_plan')
        for url_name in ('core:home', 'core:guide', 'core:constructor',
                         'core:templates', 'core:history', 'core:offline'):
            resp = self.client.get(reverse(url_name))
            self.assertEqual(resp.status_code, 200, url_name)

    def test_profile_requires_login(self):
        resp = self.client.get(reverse('core:profile'))
        self.assertEqual(resp.status_code, 302)
