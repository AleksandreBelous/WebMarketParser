// Глобальная переменная для хранения данных таблицы в виде массива объектов
let tableData = [];
// Глобальная переменная для хранения текущего состояния сортировки
let sortState = {
    column: null,
    direction: 'asc' // 'asc' или 'desc'
};

/**
 * Парсит CSV-строку и сохраняет данные в глобальную переменную tableData,
 * затем вызывает отрисовку таблицы.
 * @param {string} csvData - Содержимое CSV файла.
 */
function parseAndDisplayCsv(csvData) {
    if (!csvData) {
        tableData = [];
        document.getElementById('csv-table-container').innerHTML = '';
        return;
    }

    const rows = csvData.trim().split('\n');
    const headers = rows.shift().split(';');

    tableData = rows.map(rowStr => {
        const cells = rowStr.split(';');
        const rowObject = {};
        headers.forEach((header, index) => {
            rowObject[header] = cells[index];
        });
        return rowObject;
    });

    renderTable(); // Первая отрисовка
}

/**
 * Отрисовывает таблицу на основе данных из глобальной переменной tableData.
 */
function renderTable() {
    const container = document.getElementById('csv-table-container');
    if (tableData.length === 0) {
        container.innerHTML = '';
        return;
    }

    const headers = Object.keys(tableData[0]);

    let html = '<table class="csv-table"><thead><tr>';
    headers.forEach(header => {
        // Добавляем атрибуты для клика и стрелочку для индикации сортировки
        let sortIndicator = '';
        if (sortState.column === header) {
            sortIndicator = sortState.direction === 'asc' ? ' ▲' : ' ▼';
        }
        html += `<th data-column="${header}">${header}${sortIndicator}</th>`;
    });
    html += '</tr></thead><tbody>';

    tableData.forEach(rowObject => {
        html += '<tr>';
        headers.forEach(header => {
            html += `<td>${rowObject[header]}</td>`;
        });
        html += '</tr>';
    });

    html += '</tbody></table>';
    container.innerHTML = html;

    // Добавляем обработчики кликов на новые заголовки
    addSortEventListeners();
}

/**
 * Добавляет обработчики кликов на заголовки таблицы для сортировки.
 */
function addSortEventListeners() {
    document.querySelectorAll('#csv-table-container th').forEach(th => {
        th.addEventListener('click', () => {
            const column = th.dataset.column;
            sortTable(column);
        });
    });
}

/**
 * Сортирует данные в tableData по указанной колонке.
 * @param {string} column - Имя колонки для сортировки.
 */
function sortTable(column) {
    // Определяем направление сортировки
    if (sortState.column === column) {
        sortState.direction = sortState.direction === 'asc' ? 'desc' : 'asc';
    } else {
        sortState.column = column;
        sortState.direction = 'asc';
    }

    const direction = sortState.direction === 'asc' ? 1 : -1;

    tableData.sort((a, b) => {
        const valA = a[column];
        const valB = b[column];

        // Пробуем сравнить как числа
        const numA = parseFloat(valA);
        const numB = parseFloat(valB);

        if (!isNaN(numA) && !isNaN(numB)) {
            return (numA - numB) * direction;
        }

        // Если не числа, сравниваем как строки
        return valA.localeCompare(valB) * direction;
    });

    renderTable(); // Перерисовываем таблицу с отсортированными данными
}


// --- Исходный код для работы с сокетами ---

const socket = io();
const form = document.getElementById('parser-form');
const startButton = document.getElementById('start-button');
const logsContainer = document.getElementById('logs');
const resultContainer = document.getElementById('result');

socket.on('connect', () => {
    console.log('Успешно подключено к серверу!');
    logsContainer.innerHTML += '<div>[INFO] Соединение с сервером установлено.</div>';
});

socket.on('log_message', (msg) => {
    logsContainer.innerHTML += `<div>${msg.data}</div>`;
    logsContainer.scrollTop = logsContainer.scrollHeight;
});

socket.on('task_started', (msg) => {
    startButton.disabled = true;
    startButton.innerText = 'В процессе...';
    resultContainer.innerHTML = '';
    logsContainer.innerHTML += `<div>[SYSTEM] ${msg.data}</div>`;
});

socket.on('parsing_finished', async (msg) => { // Делаем функцию асинхронной
    startButton.disabled = false;
    startButton.innerText = 'Начать парсинг';

    if (msg.csv_url) {
        try {
            // Асинхронно загружаем CSV по URL
            const response = await fetch(msg.csv_url);
            if (!response.ok) {
                throw new Error(`Ошибка загрузки CSV: ${response.statusText}`);
            }
            const csvData = await response.text();

            parseAndDisplayCsv(csvData); // Отображаем таблицу

            let linksHTML = `<a href="${msg.csv_url}" download>Скачать CSV</a>`;

            if (msg.xlsx_url) {
                linksHTML += ` | <a href="${msg.xlsx_url}" download>Скачать XLSX</a>`;
            }

            resultContainer.innerHTML = `<h3>Готово!</h3>${linksHTML}`;
            logsContainer.innerHTML += `<div>[SUCCESS] Задача выполнена. ${linksHTML}</div>`;

        } catch (error) {
            console.error('Ошибка при загрузке или отображении CSV:', error);
            resultContainer.innerHTML = '<h3>Ошибка при отображении результата.</h3>';
        }
    } else {
        parseAndDisplayCsv(null);
        resultContainer.innerHTML = '<h3>Парсинг завершен безрезультатно.</h3>';
        logsContainer.innerHTML += `<div>[INFO] Парсинг завершен безрезультатно.</div>`;
    }

    logsContainer.scrollTop = logsContainer.scrollHeight;
});

form.addEventListener('submit', (e) => {
    e.preventDefault();
    logsContainer.innerHTML = '';

    const inputData = document.getElementById('input_data').value;
    const maxItems = document.getElementById('max_items').value;
    const pages = document.getElementById('pages').value;

    socket.emit('start_parsing', {
        input_data: inputData,
        max_items: parseInt(maxItems),
        pages: parseInt(pages)
    });
});
