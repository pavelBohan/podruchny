from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Category(models.Model):
    """Категории промптов (План урока, Тест, Письмо родителям и т.д.)"""
    name = models.CharField("Название категории", max_length=100)
    slug = models.SlugField("Слаг", unique=True)
    description = models.TextField("Описание", blank=True)
    icon = models.CharField("Иконка (emoji или class)", max_length=50, blank=True)
    order = models.PositiveIntegerField("Порядок сортировки", default=0)
    is_active = models.BooleanField("Активна", default=True)
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class PromptTemplate(models.Model):
    """Шаблоны промптов для генерации"""
    category = models.ForeignKey(
        Category, 
        on_delete=models.CASCADE, 
        related_name='templates',
        verbose_name="Категория"
    )
    name = models.CharField("Название шаблона", max_length=200)
    system_prompt = models.TextField(
        "Системный промпт (инструкция для ИИ)",
        help_text="Базовая инструкция для языковой модели"
    )
    user_prompt_template = models.TextField(
        "Шаблон пользовательского промпта",
        help_text="Используйте {variable} для подстановки ответов пользователя"
    )
    variables = models.JSONField(
        "Переменные шаблона",
        default=list,
        help_text="Список переменных: [{'name': 'subject', 'label': 'Предмет'}]"
    )
    is_active = models.BooleanField("Активен", default=True)
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    updated_at = models.DateTimeField("Дата обновления", auto_now=True)

    class Meta:
        verbose_name = "Шаблон промпта"
        verbose_name_plural = "Шаблоны промптов"
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.category.name} — {self.name}"
    
    def generate_prompt(self, context_data: dict) -> str:
        """
        Генерирует финальный промпт из шаблона и данных пользователя
        :param context_data: dict с ответами пользователя {'subject': 'Математика', 'grade': '5', ...}
        :return: str — готовый промпт
        """
        prompt = self.user_prompt_template
        
        # Подстановка переменных: {variable} -> значение
        for key, value in context_data.items():
            placeholder = f"{{{key}}}"
            if placeholder in prompt:
                prompt = prompt.replace(placeholder, str(value))
        
        # Добавляем системный промпт в начало
        full_prompt = f"{self.system_prompt}\n\n{prompt}"
        
        return full_prompt.strip()


class GeneratedPrompt(models.Model):
    """История сгенерированных промптов пользователей"""
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='prompts',
        verbose_name="Пользователь",
        null=True, 
        blank=True
    )
    template = models.ForeignKey(
        PromptTemplate,
        on_delete=models.SET_NULL,
        related_name='generations',
        verbose_name="Шаблон",
        null=True,
        blank=True
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        verbose_name="Категория"
    )
    context_data = models.JSONField(
        "Контекст (ответы пользователя)",
        default=dict
    )
    generated_prompt = models.TextField("Сгенерированный промпт")
    ai_model = models.CharField(
        "ИИ-модель", 
        max_length=50, 
        default="qwen",
        choices=[
            ('qwen', 'Qwen'),
            ('gpt-4', 'GPT-4'),
            ('claude', 'Claude'),
            ('other', 'Другая'),
        ]
    )
    is_favorite = models.BooleanField("В избранном", default=False)
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    used_at = models.DateTimeField("Дата использования", null=True, blank=True)

    class Meta:
        verbose_name = "Сгенерированный промпт"
        verbose_name_plural = "Сгенерированные промпты"
        ordering = ['-created_at']

    def __str__(self):
        return f"Промпт от {self.created_at.strftime('%d.%m.%Y')}"


class GuideArticle(models.Model):
    """Статьи гайдбука по ИИ"""
    title = models.CharField("Заголовок", max_length=200)
    slug = models.SlugField("Слаг", unique=True)
    excerpt = models.TextField("Краткое описание", max_length=300)
    content = models.TextField("Содержимое статьи")
    category = models.CharField(
        "Категория гайда",
        max_length=50,
        choices=[
            ('basics', 'Основы ИИ'),
            ('prompts', 'Промпт-инжиниринг'),
            ('tools', 'Инструменты'),
            ('education', 'ИИ в образовании'),
            ('ethics', 'Этика и безопасность'),
        ]
    )
    author = models.CharField("Автор", max_length=100, blank=True)
    published_at = models.DateTimeField("Дата публикации", default=timezone.now)
    is_published = models.BooleanField("Опубликовано", default=True)
    views = models.PositiveIntegerField("Просмотры", default=0)

    class Meta:
        verbose_name = "Статья гайдбука"
        verbose_name_plural = "Статьи гайдбука"
        ordering = ['-published_at']

    def __str__(self):
        return self.title