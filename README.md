# notion_notes_tg

![Notion](https://img.shields.io/badge/Notion-%23000000.svg?style=for-the-badge&logo=notion&logoColor=white)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Telegram](https://img.shields.io/badge/Telegram-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)

Проект по интеграции Telegram-бота и Notion API для организации
и создания заметок.

Функционал:
- Автоматическое создание ежедневных заметок
- Возможность настройки напоминания заметок
- Создание и просмотр заметок через бота

## Развертывание

Самый простой способ развертывания - инструкции из Makefile для развертывания Docker с Docker Compose.

```
make deploy
make destroy
```

## Основные команды

- /today - заметки на сегодня
- /daily - вручную создать ежедневные заметки (по умолчанию создаются в 7 утра)
- /tomorrow - заметки на завтра
- /week - заметки на неделю
- /note - интерактивное меню создания заметки

## Конфигурационный файл

Конфигурационный файл является YAML-файлом со следующими полями. [Конфиг-пример](config-sample.yaml). Он содержит следующие поля:
- token - токен интеграции Notion
- tg_token - токен Telegram-бота
- db_id - ID базы данных Notion (к которой подключено ваше представление заметок)
- tg_ids - ID Telegram-пользователей
- importance_values - значения важности заметки, которые будут использоваться
- progress_values - значения прогресса заметки
- categories_values - значения категорий заметки
- default_remind_flags - стандартные флаги напоминания
- daily_notes - список данных ежедневных заметок (заголовок, важность, категории)

## Параметры заметки

Эти параметры должны быть у вашего объекта в базе данных и только они обрабатываются
ботом:
- Importance - single-select поле
- Remind - multiselect-поле
- Progress - single-select поле
- Date - поле-дата
- Category - multiselect-поле

### Флаги напоминания (Remind)

Представляют собой multiselect-поле, где указываются различные параметры для
определения времени напоминания если заметка не завершена. Пока поддерживается единственный формат - 
точное время в формате `tЧЧ:ММ`, например `t8:15`.

## Переменные окружения

CONFIG_FILE - путь к файлу конфигурации (ст. значение: config.yaml)
