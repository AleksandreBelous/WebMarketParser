function displayCsvAsTable(csvData, containerId) {
    const container = document.getElementById(containerId);
    if (!csvData) {
        container.innerHTML = '';
        return;
    }

    const rows = csvData.trim().split('\n');
    const headers = rows.shift().split(';');

    let html = '<table class="csv-table"><thead><tr>';
    headers.forEach(header => {
        html += `<th>${header}</th>`;
    });
    html += '</tr></thead><tbody>';

    rows.forEach(rowStr => {
        const cells = rowStr.split(';'); // Упрощенный парсинг
        html += '<tr>';
        cells.forEach(cell => {
            html += `<td>${cell}</td>`;
        });
        html += '</tr>';
    });

    html += '</tbody></table>';
    container.innerHTML = html;
}

// Устанавливаем соединение с сервером
const socket = io();

const form = document.getElementById('parser-form');
const startButton = document.getElementById('start-button');
const logsContainer = document.getElementById('logs');
const resultContainer = document.getElementById('result');

// Обработчик события 'connect'
socket.on('connect', () => {
    console.log('Успешно подключено к серверу!');
    logsContainer.innerHTML += '<div>[INFO] Соединение с сервером установлено.</div>';
});

// Обработчик события 'log_message' от сервера
socket.on('log_message', (msg) => {
    logsContainer.innerHTML += `<div>${msg.data}</div>`;
    // Автоматическая прокрутка логов вниз
    logsContainer.scrollTop = logsContainer.scrollHeight;
});

// Обработчик события 'task_started' от сервера
socket.on('task_started', (msg) => {
    startButton.disabled = true;
    startButton.innerText = 'В процессе...';
    resultContainer.innerHTML = ''; // Очищаем предыдущий результат
    logsContainer.innerHTML += `<div>[SYSTEM] ${msg.data}</div>`;
});

// Обработчик события 'parsing_finished' от сервера
socket.on('parsing_finished', (msg) => {
    startButton.disabled = false;
    startButton.innerText = 'Начать парсинг';

    if (msg.result_url) {
        // Отображаем таблицу
        displayCsvAsTable(msg.csv_data, 'csv-table-container');

        // Показываем ссылку на скачивание
        const resultLink = `<a href="${msg.result_url}" download>Скачать результаты (CSV)</a>`;
        resultContainer.innerHTML = `<h3>Готово!</h3>${resultLink}`;
        logsContainer.innerHTML += `<div>[SUCCESS] Задача выполнена. <a href="${msg.result_url}" download>Скачать файл</a>.</div>`;
    } else {
        // Если результатов нет
        displayCsvAsTable(null, 'csv-table-container'); // Очищаем таблицу
        resultContainer.innerHTML = '<h3>Парсинг завершен безрезультатно.</h3>';
        logsContainer.innerHTML += `<div>[INFO] Парсинг завершен безрезультатно.</div>`;
    }

    logsContainer.scrollTop = logsContainer.scrollHeight;
});

// Отправка данных формы на сервер
form.addEventListener('submit', (e) => {
    e.preventDefault(); // Предотвращаем стандартную отправку формы
    logsContainer.innerHTML = ''; // Очищаем логи перед новым запуском

    const inputData = document.getElementById('input_data').value;
    const maxItems = document.getElementById('max_items').value;
    const pages = document.getElementById('pages').value;

    // Отправляем событие 'start_parsing' на сервер
    socket.emit('start_parsing', {
        input_data: inputData,
        max_items: parseInt(maxItems),
        pages: parseInt(pages)
    });
});
