# 📊 Структура и Логика Бота

## Архитектура

```
┌─────────────────────────────────────────────────┐
│           TELEGRAM BOT FRAMEWORK                │
│         (python-telegram-bot v20.7)             │
└─────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│              telegram_bot.py                    │
│  ┌────────────────────────────────────────┐    │
│  │  Command Handlers                      │    │
│  │  - /start (with referral code)         │    │
│  │  - Button callbacks                    │    │
│  │  - Text message handler                │    │
│  └────────────────────────────────────────┘    │
│                      │                          │
│  ┌────────────────────────────────────────┐    │
│  │  Menu System                           │    │
│  │  - Main Menu                           │    │
│  │  - Referral System                     │    │
│  │  - Profile                             │    │
│  │  - Buy Proxy                           │    │
│  │  - Information                         │    │
│  └────────────────────────────────────────┘    │
│                      │                          │
│  ┌────────────────────────────────────────┐    │
│  │  Business Logic                        │    │
│  │  - User management                     │    │
│  │  - Referral system (5₽/referral)       │    │
│  │  - Balance management                  │    │
│  │  - Proxy purchase                      │    │
│  │  - Promocode activation                │    │
│  └────────────────────────────────────────┘    │
│                      │                          │
│  ┌────────────────────────────────────────┐    │
│  │  Database Class                        │    │
│  │  - SQLite operations                   │    │
│  │  - Transaction management              │    │
│  └────────────────────────────────────────┘    │
│                      │                          │
│  ┌────────────────────────────────────────┐    │
│  │  Payment Integration                   │    │
│  │  - CryptoPayAPI class                  │    │
│  │  - Invoice creation                    │    │
│  │  - Payment verification                │    │
│  └────────────────────────────────────────┘    │
└─────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│           SQLite Database                       │
│  ┌─────────────────────────────────────────┐   │
│  │ users - профили пользователей           │   │
│  │ referrals - реферальная система         │   │
│  │ proxies - купленные прокси              │   │
│  │ transactions - история операций         │   │
│  │ promocodes - промокоды                  │   │
│  │ promocode_usage - использование         │   │
│  └─────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│         External APIs                           │
│  - Crypto Bot API (payment processing)          │
│  - Telegram Bot API (messages)                  │
└─────────────────────────────────────────────────┘
```

## Поток данных

### 1. Новый пользователь с реферальной ссылкой

```
User clicks referral link
        │
        ▼
/start <referral_code>
        │
        ▼
Database.get_or_create_user()
        │
        ├─→ Check referral code exists
        │   └─→ Find referrer
        │       └─→ Add 5₽ to referrer balance
        │           └─→ Create referral record
        │               └─→ Create transaction
        │
        ▼
Display welcome message + main menu
```

### 2. Покупка прокси

```
Click "Купить прокси"
        │
        ▼
Show proxy types menu
        │
        ▼
Select proxy type (e.g., FunTime - 26₽)
        │
        ▼
Show payment methods
        │
        ├─→ Crypto Bot
        │   └─→ Create invoice via API
        │       └─→ Show payment link
        │           └─→ User pays
        │               └─→ Webhook/Check payment
        │                   └─→ Add proxy to user
        │
        └─→ Other methods
            └─→ Show admin contact
                └─→ Manual processing
```

### 3. Реферальная система

```
User opens "Реферальная система"
        │
        ▼
Database.get_referral_stats()
        │
        ├─→ Count referrals
        ├─→ Sum total earned
        └─→ Get referral code
        │
        ▼
Generate referral link
        │
        ▼
Display statistics + link
```

## Меню навигация

```
ГЛАВНОЕ МЕНЮ
├─ 🔗 Реферальная система
│  └─ Show: stats, link, earnings
│     └─ [Назад в меню]
│
├─ 👤 Профиль
│  ├─ Show: balance, referrals, proxies
│  └─ Submenu:
│     ├─ 🎁 Промокод → Input promocode
│     ├─ 💰 Пополнить → Payment options
│     ├─ 📦 Мои прокси → List of proxies
│     └─ ⬅️ Назад → Main menu
│
├─ 🛒 Купить прокси
│  ├─ FunTime (26₽)
│  ├─ HolyWorld (36₽)
│  ├─ SpokyTime (20₽)
│  └─ Любой сервер (40₽)
│     └─ Payment method selection
│        ├─ 💎 Crypto Bot (auto)
│        ├─ ⭐ Telegram Stars (manual)
│        ├─ 🎮 FunPay (manual)
│        └─ 💳 СПБ/RU карта (manual)
│
└─ ℹ️ Информация
   └─ Show: about, how it works, support
      └─ [Назад в меню]
```

## Основные компоненты

### Database Class
- **Методы:**
  - `get_or_create_user()` - создание/получение пользователя
  - `get_referral_stats()` - статистика рефералов
  - `update_balance()` - обновление баланса
  - `add_proxy()` - добавление прокси
  - `get_user_proxies()` - список прокси
  - `use_promocode()` - активация промокода

### CryptoPayAPI Class
- **Методы:**
  - `create_invoice()` - создание счета
  - `check_invoice()` - проверка статуса

### Menu Functions
- `get_main_menu_keyboard()` - главное меню
- `get_profile_keyboard()` - меню профиля
- `get_proxy_types_keyboard()` - типы прокси
- `get_payment_methods_keyboard()` - способы оплаты

### Handler Functions
- `start_command()` - обработка /start
- `button_callback()` - обработка кнопок
- `handle_message()` - обработка текста
- `show_*()` - функции отображения меню

## Безопасность

- ✅ Все SQL запросы используют параметризацию
- ✅ Проверка существования промокодов
- ✅ Проверка дублирования использования промокодов
- ✅ Транзакционная целостность при начислении бонусов
- ✅ Валидация реферальных кодов

## Масштабируемость

Текущая архитектура поддерживает:
- ✅ Неограниченное количество пользователей
- ✅ Неограниченное количество рефералов
- ✅ Множество типов прокси
- ✅ Различные методы оплаты
- ✅ Гибкую систему промокодов

## Расширение функциональности

Легко добавить:
- Новые типы прокси (PROXY_TYPES)
- Новые методы оплаты (payment handlers)
- Дополнительные промо-акции (database tables)
- Статистику администратора (admin commands)
- Уведомления (scheduled tasks)
