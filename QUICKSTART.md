# 🚀 Быстрый старт

## Запуск бота за 3 шага

### 1. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 2. Настройка (опционально)
Откройте `telegram_bot.py` и измените:
- `BOT_TOKEN` - ваш токен бота (уже установлен)
- `CRYPTO_BOT_TOKEN` - токен Crypto Bot API (уже установлен)
- `ADMIN_USERNAME` - имя администратора (уже установлен)

**Текущие настройки:**
- Bot Token: `526566:AAQFBfnPypXgTD4EnzsAOuhlwJ8PJpazj9L`
- Crypto Bot Token: `8321595208:AAE7m_cXGH0IV7V84e-ch26eEz659PItSho`
- Admin: `@ARBUZ_ANSWERS_maneger`

### 3. Запуск
```bash
python telegram_bot.py
```

Готово! Бот запущен и готов к работе! 🎉

## Тестирование

### Тест базы данных
```bash
python test_database.py
```

### Добавление промокодов
```bash
python add_promocodes.py
```

## Использование бота

1. Найдите бота в Telegram
2. Нажмите `/start`
3. Выберите нужное действие из меню

### Основные функции:
- **🔗 Реферальная система** - получите свою ссылку и зарабатывайте
- **👤 Профиль** - ваша статистика и баланс
- **🛒 Купить прокси** - покупка прокси для Minecraft
- **ℹ️ Информация** - помощь и информация

## Структура проекта

```
telegrambot/
├── telegram_bot.py       # Основной файл бота (ВСЕ В ОДНОМ ФАЙЛЕ!)
├── requirements.txt      # Зависимости
├── README.md            # Полная документация
├── QUICKSTART.md        # Этот файл
├── test_database.py     # Тесты базы данных
├── add_promocodes.py    # Добавление промокодов
├── .gitignore          # Исключения Git
└── bot_database.db     # База данных (создается автоматически)
```

## Возможные проблемы

### Ошибка "ModuleNotFoundError: No module named 'telegram'"
**Решение:** Установите зависимости
```bash
pip install -r requirements.txt
```

### Бот не отвечает
**Решение:** 
1. Проверьте токен бота
2. Убедитесь что бот запущен
3. Проверьте интернет-соединение

### Ошибка "Permission denied" при создании БД
**Решение:** Проверьте права на запись в директории
```bash
chmod 755 .
```

## Дополнительные команды

### Создать промокоды вручную
Откройте Python консоль:
```python
from add_promocodes import add_promocode
add_promocode("MYCODE", 50.0, 100)  # код, сумма, использования
```

### Посмотреть базу данных
```bash
sqlite3 bot_database.db
sqlite> SELECT * FROM users;
sqlite> .quit
```

## Поддержка

Администратор: @ARBUZ_ANSWERS_maneger

## Тестовая проверка

Убедитесь что все работает:
```bash
# 1. Тест синтаксиса
python3 -m py_compile telegram_bot.py

# 2. Тест базы данных
python3 test_database.py

# 3. Запуск бота
python3 telegram_bot.py
```

Все команды должны выполниться без ошибок!

---

**Важно:** Бот полностью функционален и готов к работе. Все фичи реализованы в одном файле `telegram_bot.py` как и требовалось! ✨
