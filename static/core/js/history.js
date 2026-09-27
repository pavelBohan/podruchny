/**
 * Оффлайн-история промптов (страница /history/)
 * Читает данные из localStorage, которые сохраняет constructor.js
 * через PromptGenerator.savePrompt(). Работает без сети.
 */

(function () {
    'use strict';

    const listEl = document.getElementById('history-list');
    if (!listEl) return;

    const generator = new window.PromptGenerator();

    function escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = String(str == null ? '' : str);
        return div.innerHTML;
    }

    function formatDate(iso) {
        try {
            return new Date(iso).toLocaleString('ru-RU', {
                day: '2-digit', month: '2-digit', year: 'numeric',
                hour: '2-digit', minute: '2-digit',
            });
        } catch (e) {
            return iso;
        }
    }

    function render() {
        const history = generator.getHistory(100);

        if (!history.length) {
            listEl.innerHTML =
                '<p class="empty-state">История пуста. ' +
                '<a href="/constructor/">Создайте первый промпт →</a></p>';
            return;
        }

        listEl.innerHTML = history.map(function (item) {
            const preview = (item.prompt || '').slice(0, 200);
            return (
                '<div class="card prompt-item" data-id="' + item.id + '">' +
                    '<div class="prompt-header">' +
                        '<span class="prompt-category">' +
                            escapeHtml(item.templateName || item.category || 'Промпт') +
                        '</span>' +
                        '<span class="prompt-date">' + formatDate(item.timestamp) + '</span>' +
                    '</div>' +
                    '<div class="prompt-content"><pre>' + escapeHtml(preview) + '…</pre></div>' +
                    '<div class="prompt-actions">' +
                        '<button class="btn btn--outline btn--sm" data-action="copy">' +
                            '📋 Копировать</button>' +
                        '<a class="btn btn--secondary btn--sm" data-action="open" target="_blank" rel="noopener" ' +
                            'href="https://chat.qwen.ai/">🤖 В Qwen</a>' +
                        '<button class="btn btn--danger btn--sm" data-action="delete">' +
                            '🗑️ Удалить</button>' +
                    '</div>' +
                '</div>'
            );
        }).join('');
    }

    // Делегирование событий для кнопок в списке
    listEl.addEventListener('click', function (e) {
        const btn = e.target.closest('[data-action]');
        if (!btn) return;
        const card = btn.closest('.prompt-item');
        const id = Number(card.dataset.id);
        const action = btn.dataset.action;

        if (action === 'copy') {
            const item = generator.getHistory(100).find(function (h) { return h.id === id; });
            navigator.clipboard.writeText(item ? item.prompt : '')
                .then(function () {
                    btn.textContent = '✅ Скопировано!';
                    setTimeout(function () { btn.textContent = '📋 Копировать'; }, 2000);
                })
                .catch(function () { alert('Не удалось скопировать'); });
        }

        if (action === 'delete') {
            if (confirm('Удалить этот промпт из истории?')) {
                generator.deletePrompt(id);
                render();
            }
        }
    });

    // Полная очистка истории
    const clearBtn = document.getElementById('clear-history-btn');
    if (clearBtn) {
        clearBtn.addEventListener('click', function () {
            if (confirm('Удалить ВСЮ историю промптов с этого устройства?')) {
                localStorage.removeItem('prompt_history');
                render();
            }
        });
    }

    render();
})();
