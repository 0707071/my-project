class Analyzer {
    constructor() {
        this.promptMaster = new PromptMaster();
        this.settings = null;
        this.tableData = null;
        
        // Инициализация UI элементов
        this.initUI();
        this.initEventHandlers();
    }

    initUI() {
        // Получаем элементы интерфейса
        this.promptInput = document.getElementById('promptInput');
        this.columnsInput = document.getElementById('columnsInput');
        this.generateBtn = document.getElementById('generatePrompt');
        this.analyzeBtn = document.getElementById('analyzeData');
    }

    initEventHandlers() {
        // Обработчик загрузки файла
        document.getElementById('fileUpload').addEventListener('change', async (e) => {
            const file = e.target.files[0];
            if (!file) return;
            
            const formData = new FormData();
            formData.append('file', file);
            
            try {
                const response = await fetch('/analyzer/upload', {
                    method: 'POST',
                    body: formData
                });
                
                if (!response.ok) throw new Error('Upload failed');
                this.tableData = await response.json();
                
                // Активируем кнопки после загрузки
                this.generateBtn.disabled = false;
                this.analyzeBtn.disabled = false;
                
            } catch (error) {
                console.error('Upload error:', error);
                alert('Failed to upload file');
            }
        });

        // Обработчик генерации промпта
        this.generateBtn.addEventListener('click', async () => {
            if (!this.tableData) {
                alert('Please upload data first');
                return;
            }
            
            try {
                const response = await fetch('/analyzer/generate_prompt', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        current_prompt: this.promptInput.value,
                        current_columns: this.columnsInput.value.split('\n').filter(Boolean),
                        table_data: this.tableData
                    })
                });
                
                if (!response.ok) throw new Error('Generation failed');
                const result = await response.json();
                
                // Обновляем поля промпта и колонок
                this.promptInput.value = result.prompt;
                this.columnsInput.value = result.columns.join('\n');
                
            } catch (error) {
                console.error('Generation error:', error);
                alert('Failed to generate prompt');
            }
        });
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    window.analyzer = new Analyzer();
}); 