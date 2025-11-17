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

    // прямо перед container.innerHTML = html;
    console.debug('[table] rendering table, html headers snippet:', html.slice(0, 400));

    container.innerHTML = html;

    // Добавляем обработчики кликов на новые заголовки
    // setTimeout(addSortEventListeners, 0); // старое
    addSortEventListeners(); // вызывать сразу — надежнее на разных окружениях
}

/**
 * Добавляет обработчики кликов на заголовки таблицы для сортировки.
 */
function addSortEventListeners() {
    const ths = document.querySelectorAll('#csv-table-container th');
    console.debug('[table] addSortEventListeners called, headers count =', ths.length, 'sortState=', sortState);
    if (!ths || ths.length === 0) {
        console.warn('[table] no <th> found in #csv-table-container — check that table markup contains <thead> and <th data-column="...">');
    }
    ths.forEach(th => {
        // защищаем от двойного навешивания
        if (th.__hasSortHandler) return;
        th.__hasSortHandler = true;
        th.addEventListener('click', () => {
            const column = th.dataset.column;
            console.debug('[table] header clicked:', column);
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

socket.on('parsing_finished', (msg) => {
    startButton.disabled = false;
    startButton.innerText = 'Начать парсинг';

    if (msg.result_url) {
        parseAndDisplayCsv(msg.csv_data); // Используем новую функцию
        const resultLink = `<a href="${msg.result_url}" download>Скачать результаты (CSV)</a>`;
        resultContainer.innerHTML = `<h3>Готово!</h3>${resultLink}`;
        logsContainer.innerHTML += `<div>[SUCCESS] Задача выполнена. <a href="${msg.result_url}" download>Скачать файл</a>.</div>`;
    } else {
        parseAndDisplayCsv(null); // Очищаем таблицу
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

// --- Надёжное делегирование и экспорт sortTable ---
// Поместите этот код **после** определения функции sortTable и после основной логики файла.

try {
  // Экспортируем sortTable в window (на случай, если она объявлена локально)
  if (typeof sortTable === 'function') {
    window.sortTable = sortTable;
    console.debug('[table] sortTable exported to window');
  } else {
    console.debug('[table] sortTable function not found at export time. It may be defined later.');
  }

  // Навешиваем делегирование на контейнер - работает независимо от перерисовок таблицы
  document.addEventListener('DOMContentLoaded', function () {
    const container = document.getElementById('csv-table-container') || document.querySelector('.csv-table')?.parentElement || document.body;
    if (!container) {
      console.warn('[table] csv container not found for delegation');
      return;
    }

    container.addEventListener('click', function (e) {
      const th = e.target.closest('th');
      if (!th) return;
      const column = th.dataset.column || th.getAttribute('data-column');
      if (!column) return;
      console.debug('[table] delegated header click:', column);

      // Вызов сортировки через глобальную точку входа
      if (typeof window.sortTable === 'function') {
        try {
          window.sortTable(column);
        } catch (err) {
          console.error('[table] sortTable threw error:', err);
        }
      } else if (typeof sortTable === 'function') {
        try {
          sortTable(column);
        } catch (err) {
          console.error('[table] local sortTable threw error:', err);
        }
      } else {
        console.error('[table] sortTable not found');
      }
    }, false);
  });
} catch (err) {
  console.error('[table] delegation setup failed:', err);
}
