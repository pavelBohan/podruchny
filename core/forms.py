from django import forms


class PromptConstructorForm(forms.Form):
    """Форма конструктора промптов"""
    
    CATEGORY_CHOICES = [
        ('lesson_plan', '📋 План урока'),
        ('test', '📝 Тесты и задания'),
        ('parent_letter', '✉️ Письмо родителям'),
        ('methodology', '📚 Методические материалы'),
        ('assessment', '⭐ Оценивание'),
        ('extracurricular', '🎭 Внеурочная деятельность'),
    ]
    
    category = forms.ChoiceField(
        label="Выберите категорию помощи",
        choices=CATEGORY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-input', 'id': 'category-select'})
    )
    
    # Динамические поля будут добавляться через JavaScript
    # Здесь только общие поля
    
    subject = forms.CharField(
        label="Предмет",
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Например: Математика'})
    )
    
    grade = forms.CharField(
        label="Класс",
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Например: 5 "Б"'})
    )
    
    topic = forms.CharField(
        label="Тема урока/задания",
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Например: Дроби'})
    )
    
    context = forms.CharField(
        label="Дополнительный контекст",
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-input', 
            'rows': 4,
            'placeholder': 'Особенности класса, цели урока, предпочтения по формату...'
        })
    )
    
    tone = forms.ChoiceField(
        label="Тон ответа",
        choices=[
            ('professional', '🎓 Профессиональный'),
            ('friendly', '😊 Дружелюбный'),
            ('strict', '⚖️ Строгий'),
            ('motivational', '🔥 Мотивирующий'),
        ],
        initial='professional',
        widget=forms.RadioSelect(attrs={'class': 'form-radio'})
    )