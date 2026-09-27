/**
 * Клиентская генерация промптов (оффлайн-режим)
 * Заменяет серверную логику Django + C#
 */

class PromptGenerator {
    constructor() {
        this.templates = [];
        this.categories = [];
        this.loaded = false;
    }

    // Загрузка данных из JSON-файлов
    async loadData() {
        try {
            const [categoriesRes, templatesRes] = await Promise.all([
                fetch('/static/data/categories.json'),
                fetch('/static/data/templates.json')
            ]);
            
            this.categories = await categoriesRes.json();
            this.templates = await templatesRes.json();
            this.loaded = true;
            return true;
        } catch (error) {
            console.error('Failed to load data:', error);
            return false;
        }
    }

    // Валидация входных данных (замена C# модуля)
    validateInput(data) {
        const errors = [];
        const validated = {};

        // Обязательные поля
        ['subject', 'grade', 'topic'].forEach(field => {
            if (!data[field] || !data[field].trim()) {
                errors.push(`Поле "${field}" обязательно`);
            } else {
                validated[field] = data[field].trim();
            }
        });

        // Очистка и ограничение контекста
        if (data.additional_context) {
            const ctx = data.additional_context.trim();
            validated.additional_context = ctx.length > 500 
                ? ctx.substring(0, 500) + '...' 
                : ctx;
        }

        // Валидация тона
        const validTones = ['professional', 'friendly', 'strict', 'motivational'];
        validated.tone = validTones.includes(data.tone) ? data.tone : 'professional';

        return { errors, validated, isValid: errors.length === 0 };
    }

    // Генерация промпта из шаблона
    generatePrompt(templateId, contextData) {
        const template = this.templates.find(t => t.id === templateId);
        if (!template) {
            throw new Error('Шаблон не найден');
        }

        let prompt = template.user_prompt_template;

        // Подстановка переменных: {variable} -> значение
        Object.entries(contextData).forEach(([key, value]) => {
            const placeholder = new RegExp(`\\{${key}\\}`, 'g');
            prompt = prompt.replace(placeholder, value || '');
        });

        // Добавляем системный промпт
        const fullPrompt = `${template.system_prompt}\n\n${prompt}`;

        return fullPrompt.trim();
    }

    // Поиск шаблона по категории
    getTemplatesByCategory(categorySlug) {
        return this.templates.filter(t => t.category__slug === categorySlug);
    }

    // Сохранение промпта в localStorage (оффлайн-история)
    savePrompt(promptData) {
        const history = JSON.parse(localStorage.getItem('prompt_history') || '[]');
        
        const entry = {
            id: Date.now(),
            timestamp: new Date().toISOString(),
            ...promptData
        };
        
        history.unshift(entry); // Добавляем в начало
        
        // Ограничиваем историю 100 записями
        if (history.length > 100) {
            history.pop();
        }
        
        localStorage.setItem('prompt_history', JSON.stringify(history));
        return entry.id;
    }

    // Получение истории промптов
    getHistory(limit = 50) {
        const history = JSON.parse(localStorage.getItem('prompt_history') || '[]');
        return history.slice(0, limit);
    }

    // Удаление промпта из истории
    deletePrompt(id) {
        const history = JSON.parse(localStorage.getItem('prompt_history') || '[]');
        const filtered = history.filter(item => item.id !== id);
        localStorage.setItem('prompt_history', JSON.stringify(filtered));
    }
}

// Экспорт для использования в других модулях
window.PromptGenerator = PromptGenerator;