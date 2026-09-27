/**
 * Общие скрипты интерфейса «Подручный» (main.js)
 * Индикатор оффлайн-режима и мелкие UX-улучшения.
 */

(function () {
    'use strict';

    // --- Индикатор состояния сети (онлайн/оффлайн) ---
    function updateNetworkBadge() {
        let badge = document.getElementById('network-badge');
        if (!badge) {
            badge = document.createElement('div');
            badge.id = 'network-badge';
            badge.style.cssText =
                'position:fixed;bottom:16px;left:16px;z-index:9999;' +
                'padding:6px 14px;border-radius:20px;font-family:Inter,sans-serif;' +
                'font-size:13px;color:#fff;display:none;box-shadow:0 2px 8px rgba(0,0,0,.2);';
            document.body.appendChild(badge);
        }

        if (navigator.onLine) {
            badge.style.display = 'none';
        } else {
            badge.textContent = '📡 Оффлайн-режим — конструктор работает';
            badge.style.display = 'block';
            badge.style.background = '#045670';
        }
    }

    window.addEventListener('online', updateNetworkBadge);
    window.addEventListener('offline', updateNetworkBadge);
    document.addEventListener('DOMContentLoaded', updateNetworkBadge);

    // --- Плавная прокрутка к якорям ---
    document.addEventListener('click', function (e) {
        const link = e.target.closest('a[href^="#"]');
        if (link && link.getAttribute('href').length > 1) {
            const target = document.querySelector(link.getAttribute('href'));
            if (target) {
                e.preventDefault();
                target.scrollIntoView({ behavior: 'smooth' });
            }
        }
    });
})();
