document.addEventListener('DOMContentLoaded', function() {
    // Находим все кнопки анализа
    document.querySelectorAll('.analyze-btn').forEach(button => {
        button.addEventListener('click', function() {
            // Находим соответствующий input для файла
            const fileInput = this.closest('form').querySelector('.cleaned-file-input');
            fileInput.click();
        });
    });

    // Обработка выбора файла
    document.querySelectorAll('.cleaned-file-input').forEach(input => {
        input.addEventListener('change', function() {
            if (this.files.length > 0) {
                const form = this.closest('form');
                const button = form.querySelector('.analyze-btn');
                const originalText = button.innerHTML;
                
                // Показываем индикатор загрузки
                button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Uploading...';
                button.disabled = true;
                
                // Создаем FormData и добавляем файл
                const formData = new FormData();
                formData.append('cleaned_file', this.files[0]);
                formData.append('search_query_id', form.querySelector('input[name="search_query_id"]').value);
                formData.append('mode', form.querySelector('input[name="mode"]').value);
                
                // Отправляем форму через fetch
                fetch(form.action, {
                    method: 'POST',
                    body: formData
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    return response.text();
                })
                .then(html => {
                    console.log('Server response:', html); // Для отладки
                    
                    // Проверяем, есть ли в ответе редирект
                    const match = html.match(/<meta http-equiv="refresh" content="0; url=([^"]+)">/);
                    if (match) {
                        window.location.href = match[1];
                        return;
                    }
                    
                    // Проверяем, является ли ответ страницей статуса задачи
                    if (html.includes('<title>Task Status - Karhuno Analysis System</title>')) {
                        // Извлекаем URL из кнопки "Back to Client"
                        const taskStatusMatch = html.match(/href="([^"]+)"\s+class="btn btn-secondary">Back to Client/);
                        if (taskStatusMatch) {
                            // Получаем базовый URL из кнопки "Back to Client"
                            const baseUrl = taskStatusMatch[1];
                            // Извлекаем taskId из скрипта
                            const taskIdMatch = html.match(/const taskId = (\d+);/);
                            if (taskIdMatch) {
                                // Формируем URL страницы статуса задачи
                                const taskStatusUrl = `/task/${taskIdMatch[1]}`;
                                window.location.href = taskStatusUrl;
                                return;
                            }
                        }
                    }
                    
                    // Если нет редиректа, проверяем наличие flash сообщений
                    const parser = new DOMParser();
                    const doc = parser.parseFromString(html, 'text/html');
                    const flashMessages = doc.querySelectorAll('.alert');
                    
                    if (flashMessages.length > 0) {
                        // Показываем первое сообщение об ошибке
                        const message = flashMessages[0].textContent.trim();
                        console.error('Flash message:', message);
                        alert(message);
                    } else {
                        console.error('No flash messages found in response');
                        console.error('Response HTML:', html);
                        alert('Ошибка обработки файла. Проверьте консоль для деталей.');
                    }
                    button.innerHTML = originalText;
                    button.disabled = false;
                })
                .catch(error => {
                    console.error('Error:', error);
                    console.error('Error details:', error.stack);
                    button.innerHTML = originalText;
                    button.disabled = false;
                    alert(`Ошибка загрузки файла: ${error.message}`);
                });
            }
        });
    });
});

// Добавляем стили для форм в дропдауне
document.head.insertAdjacentHTML('beforeend', `
    <style>
        .dropdown-menu {
            z-index: 1050;  /* Увеличиваем z-index чтобы меню было поверх всего */
        }
        
        .btn-group {
            position: static;  /* Позволяет дропдауну выходить за пределы группы */
        }
        
        .dropdown-item-form {
            padding: 0;
            margin: 0;
        }
        
        .dropdown-item-form button {
            width: 100%;
            text-align: left;
            border: none;
            background: none;
            padding: .5rem 1rem;
            color: #666;  /* Делаем цвет текста немного серым для debug опций */
            font-size: 0.875rem;
        }
        
        .dropdown-item-form button:hover {
            background-color: #f8f9fa;
            color: #333;
        }
        
        .dropdown-item-form button i {
            color: #999;  /* Иконка жучка серая */
        }
        
        .dropdown-item-form button:hover i {
            color: #666;  /* При наведении иконка темнеет */
        }
        
        /* Стили для split button */
        .dropdown-toggle-split {
            padding-left: 0.5rem;
            padding-right: 0.5rem;
        }
        
        .dropdown-toggle-split::after {
            margin-left: 0;
        }
        
        /* Стили для состояния загрузки */
        .analyze-btn:disabled {
            opacity: 0.7;
            cursor: not-allowed;
        }
        
        .analyze-btn .fa-spin {
            display: inline-block;
            animation: fa-spin 2s infinite linear;
        }
        
        @keyframes fa-spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
`); 