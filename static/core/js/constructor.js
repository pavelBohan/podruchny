/**
 * Пошаговая логика конструктора промптов «Подручный»
 * Работает полностью оффлайн: данные берутся из static/data/*.json
 * (через PromptGenerator), серверный API — только необязательный бонус.
 */

(function () {
    'use strict';

    const form = document.getElementById('prompt-form');
    if (!form) return; // скрипт подключён не на странице конструктора

    let currentStep = 1;
    const STEP_NAMES = { 1: 'category', 2: 'basic', 3: 'context' };

    // Предустановки из query-параметров (?category=slug&template=id),
    // которые формирует ссылка из библиотеки шаблонов
    const urlParams = new URLSearchParams(window.location.search);
    const presetCategory = urlParams.get('category') || '';
    const presetTemplateId = parseInt(urlParams.get('template'), 10) || null;

    let selectedTemplateId = presetTemplateId;

    // Глобальный генератор (оффлайн-ядро)
    const generator = new window.PromptGenerator();
    window.podruchnyGenerator = generator; // доступ из консоли для отладки

    generator.loadData().then((ok) => {
        if (!ok) {
            console.warn('Не удалось загрузить JSON-данные, ждём серверный режим.');
            return;
        }
        applyPresets();
    });

    function applyPresets() {
        const categorySelect = document.getElementById('category-select');
        if (!presetCategory) return;

        const option = categorySelect.querySelector('option[value="' + presetCategory + '"]');
        if (option) {
            categorySelect.value = presetCategory;
            renderTemplateChoice();
            showStep(2);
        }
    }

    // Шаг 1.5: выбор конкретного шаблона внутри категории
    function renderTemplateChoice() {
        const container = document.getElementById('template-choice');
        if (!container) return;

        const slug = document.getElementById('category-select').value;
        const templates = generator.getTemplatesByCategory(slug);

        if (!generator.loaded) {
            container.innerHTML = '<p class="hint">Данные ещё загружаются…</p>';
            return;
        }
        if (!templates.length) {
            container.style.display = 'none';
            container.innerHTML = '';
            selectedTemplateId = null;
            return;
        }

        container.style.display = 'block';
        container.innerHTML =
            '<label class="form-label">Выберите шаблон</label>' +
            templates.map(function (t, i) {
                return '<label class="radio-group__item template-option">' +
                    '<input type="radio" name="template-choice" value="' + t.id + '"' +
                    ((selectedTemplateId === t.id || (!selectedTemplateId && i === 0)) ? ' checked' : '') + '>' +
                    ' ' + t.name + '</label>';
            }).join('');

        container.querySelectorAll('input[name="template-choice"]').forEach(function (radio) {
            radio.addEventListener('change', function () {
                selectedTemplateId = parseInt(this.value, 10);
            });
        });
    }

    function showStep(step) {
        Object.values(STEP_NAMES).forEach((name) => {
            const el = document.getElementById(`step-${name}`);
            if (el) el.style.display = 'none';
        });
        const target = document.getElementById(`step-${STEP_NAMES[step]}`);
        if (target) target.style.display = 'block';
        currentStep = step;
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    function validateStep(step) {
        if (step === 1) {
            const category = document.getElementById('category-select').value;
            if (!category) {
                alert('Пожалуйста, выберите категорию');
                return false;
            }
        }
        if (step === 2) {
            const subject = form.querySelector('[name="subject"]').value.trim();
            const grade = form.querySelector('[name="grade"]').value.trim();
            const topic = form.querySelector('[name="topic"]').value.trim();
            if (!subject || !grade || !topic) {
                alert('Пожалуйста, заполните все обязательные поля');
                return false;
            }
        }
        return true;
    }

    const categorySelectEl = document.getElementById('category-select');
    if (categorySelectEl) {
        categorySelectEl.addEventListener('change', function () {
            selectedTemplateId = null;
            renderTemplateChoice();
        });
    }

    window.nextStep = function (step) {
        if (!validateStep(currentStep)) return;
        showStep(step);
    };

    window.prevStep = function (step) {
        showStep(step);
    };

    function collectFormData() {
        const extraContext = form.querySelector('[name="context"]').value;
        return {
            category: document.getElementById('category-select').value,
            template_id: selectedTemplateId,
            context: {
                subject: form.querySelector('[name="subject"]').value,
                grade: form.querySelector('[name="grade"]').value,
                topic: form.querySelector('[name="topic"]').value,
                additional_context: extraContext,
                context: extraContext,
                tone: form.querySelector('input[name="tone"]:checked').value,
            },
        };
    }

    // Оффлайн-генерация через PromptGenerator + localStorage
    function generateOffline(data) {
        const { errors, validated, isValid } = generator.validateInput(data.context);
        if (!isValid) {
            throw new Error(errors.join('; '));
        }

        const templates = generator.getTemplatesByCategory(data.category);
        if (!templates.length) {
            throw new Error('Для выбранной категории шаблоны не найдены. ' +
                'Выполните python manage.py export_data');
        }

        const chosen = templates.find(function (t) { return t.id === data.template_id; })
            || templates[0];

        const context = Object.assign({}, validated, {
            additional_context: data.context.additional_context || '',
            context: data.context.additional_context || '',
        });

        const prompt = generator.generatePrompt(chosen.id, context);

        generator.savePrompt({
            category: data.category,
            templateId: templates[0].id,
            templateName: templates[0].name,
            context: context,
            prompt: prompt,
        });

        return { prompt: prompt, qwen_url: 'https://chat.qwen.ai/' };
    }

    // Онлайн-генерация через Django API (необязательна)
    async function generateOnline(data) {
        const response = await fetch('/constructor/generate/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': form.querySelector('[name=csrfmiddlewaretoken]').value,
            },
            body: JSON.stringify(data),
        });
        if (!response.ok) throw new Error('Сервер недоступен');
        const result = await response.json();
        if (!result.success) throw new Error(result.error || 'Ошибка сервера');
        return result;
    }

    function showResult(result) {
        document.getElementById('prompt-output').textContent = result.prompt;
        const qwenLink = document.getElementById('qwen-link');
        if (qwenLink) qwenLink.href = result.qwen_url || 'https://chat.qwen.ai/';
        document.getElementById('result-section').style.display = 'block';
        form.style.display = 'none';
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    form.addEventListener('submit', async function (e) {
        e.preventDefault();

        const submitBtn = form.querySelector('button[type="submit"]');
        submitBtn.disabled = true;
        submitBtn.textContent = 'Генерация...';

        const data = collectFormData();
        let result = null;

        // 1) Пробуем сервер (если есть сеть)
        try {
            result = await generateOnline(data);
        } catch (serverError) {
            console.warn('Сервер недоступен, переключаемся на оффлайн:', serverError.message);
        }

        // 2) Оффлайн-фолбэк через PromptGenerator
        if (!result) {
            try {
                result = generateOffline(data);
            } catch (offlineError) {
                alert('Не удалось сгенерировать промпт: ' + offlineError.message);
            }
        }

        if (result) showResult(result);

        submitBtn.disabled = false;
        submitBtn.textContent = '✨ Сгенерировать промпт';
    });

    // Копирование промпта с визуальной обратной связью
    window.copyPrompt = function (event) {
        const promptText = document.getElementById('prompt-output').textContent;
        const btn = event ? event.target : document.querySelector('.btn--copy');
        const originalText = btn ? btn.innerHTML : null;

        navigator.clipboard.writeText(promptText).then(() => {
            if (btn) {
                btn.innerHTML = '✅ Скопировано!';
                setTimeout(() => { btn.innerHTML = originalText; }, 2000);
            }
        }).catch(() => {
            alert('❌ Не удалось скопировать. Выделите текст и нажмите Ctrl+C');
        });
    };

    // Сброс формы
    window.resetForm = function () {
        document.getElementById('result-section').style.display = 'none';
        form.reset();
        form.style.display = 'block';
        showStep(1);
    };

    showStep(1);
})();
