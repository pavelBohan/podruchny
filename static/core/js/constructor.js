let currentStep = 1;
const totalSteps = 3;

function nextStep(step) {
    // Валидация текущего шага
    if (!validateStep(currentStep)) return;
    
    // Скрываем текущий шаг
    document.getElementById(`step-${getStepName(currentStep)}`).style.display = 'none';
    
    // Показываем следующий
    document.getElementById(`step-${getStepName(step)}`).style.display = 'block';
    currentStep = step;
}

function prevStep(step) {
    document.getElementById(`step-${getStepName(currentStep)}`).style.display = 'none';
    document.getElementById(`step-${getStepName(step)}`).style.display = 'block';
    currentStep = step;
}

function getStepName(num) {
    const steps = {1: 'category', 2: 'basic', 3: 'context'};
    return steps[num];
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
        const subject = document.querySelector('[name="subject"]').value;
        const grade = document.querySelector('[name="grade"]').value;
        const topic = document.querySelector('[name="topic"]').value;
        
        if (!subject || !grade || !topic) {
            alert('Пожалуйста, заполните все обязательные поля');
            return false;
        }
    }
    return true;
}

// Обработка формы
document.getElementById('prompt-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const submitBtn = this.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Генерация...';
    
    // Собираем данные
    const formData = {
        category: document.getElementById('category-select').value,
        context: {
            subject: document.querySelector('[name="subject"]').value,
            grade: document.querySelector('[name="grade"]').value,
            topic: document.querySelector('[name="topic"]').value,
            additional_context: document.querySelector('[name="context"]').value,
            tone: document.querySelector('input[name="tone"]:checked').value,
        }
    };
    
    try {
        const response = await fetch('{% url "core:generate_prompt" %}', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            },
            body: JSON.stringify(formData),
        });
        
        const result = await response.json();
        
        // Внутри fetch().then() после проверки result.success:

        if (result.success) {
            // Показываем результат
            document.getElementById('prompt-output').textContent = result.prompt;
            
            // === ДОБАВЬТЕ ЭТУ СТРОКУ ===
            document.getElementById('qwen-link').href = result.qwen_url;
            // ===========================
            
            document.getElementById('result-section').style.display = 'block';
            
            // Скрываем форму
            this.closest('.constructor-form').style.display = 'none';
        } else {
            alert('Ошибка: ' + (result.error || 'Неизвестная ошибка'));
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Произошла ошибка при генерации промпта');
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = '✨ Сгенерировать промпт';
    }
});

// Копирование промпта с визуальной обратной связью
function copyPrompt() {
    const promptText = document.getElementById('prompt-output').textContent;
    const btn = event.target;
    const originalText = btn.innerHTML;
    
    navigator.clipboard.writeText(promptText).then(() => {
        // Визуальное подтверждение
        btn.innerHTML = '✅ Скопировано!';
        btn.style.backgroundColor = 'var(--success-green)';
        
        // Возврат кнопки через 2 секунды
        setTimeout(() => {
            btn.innerHTML = originalText;
            btn.style.backgroundColor = '';
        }, 2000);
    }).catch(err => {
        console.error('Copy error:', err);
        alert('❌ Не удалось скопировать. Выделите текст и нажмите Ctrl+C');
    });
}

// Сброс формы
function resetForm() {
    document.getElementById('result-section').style.display = 'none';
    document.querySelector('.constructor-form').style.display = 'block';
    document.getElementById('prompt-form').reset();
    nextStep(1);
}