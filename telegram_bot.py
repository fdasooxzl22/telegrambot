#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram Bot для продажи прокси для Minecraft серверов
Функции: реферальная система, профиль, покупка прокси, оплата через Crypto Bot
"""

import logging
import sqlite3
import hashlib
import requests
from datetime import datetime
from typing import Optional, Dict, Any
import json

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# Конфигурация
BOT_TOKEN = "526566:AAQFBfnPypXgTD4EnzsAOuhlwJ8PJpazj9L"
CRYPTO_BOT_TOKEN = "8321595208:AAE7m_cXGH0IV7V84e-ch26eEz659PItSho"
ADMIN_USERNAME = "@ARBUZ_ANSWERS_maneger"
REFERRAL_BONUS = 5.0  # Бонус за реферала в рублях

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Прокси типы и цены
PROXY_TYPES = {
    'funtime': {'name': 'FunTime', 'price': 26},
    'holyworld': {'name': 'HolyWorld', 'price': 36},
    'spokytime': {'name': 'SpokyTime', 'price': 20},
    'anyserver': {'name': 'Любой сервер', 'price': 40}
}


class Database:
    """Класс для работы с базой данных"""
    
    def __init__(self, db_name='bot_database.db'):
        self.db_name = db_name
        self.init_db()
    
    def get_connection(self):
        """Создает подключение к БД"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db(self):
        """Инициализация базы данных"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Таблица пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                balance REAL DEFAULT 0,
                referrer_id INTEGER,
                referral_code TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица рефералов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS referrals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id INTEGER,
                referred_id INTEGER,
                bonus_paid REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (referrer_id) REFERENCES users(user_id),
                FOREIGN KEY (referred_id) REFERENCES users(user_id)
            )
        ''')
        
        # Таблица прокси
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS proxies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                proxy_type TEXT,
                proxy_data TEXT,
                price REAL,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Таблица транзакций
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount REAL,
                transaction_type TEXT,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Таблица промокодов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS promocodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE,
                amount REAL,
                uses_left INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица использованных промокодов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS promocode_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                code TEXT,
                amount REAL,
                used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_or_create_user(self, user_id: int, username: str = None, 
                          first_name: str = None, last_name: str = None,
                          referrer_code: str = None) -> Dict[str, Any]:
        """Получить или создать пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = cursor.fetchone()
        
        if user:
            conn.close()
            return dict(user)
        
        # Создаем нового пользователя
        referral_code = self._generate_referral_code(user_id)
        referrer_id = None
        
        # Проверяем реферальный код
        if referrer_code:
            cursor.execute('SELECT user_id FROM users WHERE referral_code = ?', (referrer_code,))
            referrer = cursor.fetchone()
            if referrer:
                referrer_id = referrer['user_id']
        
        cursor.execute('''
            INSERT INTO users (user_id, username, first_name, last_name, referral_code, referrer_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, username, first_name, last_name, referral_code, referrer_id))
        
        # Если есть реферер, начисляем бонус
        if referrer_id:
            cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?',
                         (REFERRAL_BONUS, referrer_id))
            cursor.execute('''
                INSERT INTO referrals (referrer_id, referred_id, bonus_paid)
                VALUES (?, ?, ?)
            ''', (referrer_id, user_id, REFERRAL_BONUS))
            cursor.execute('''
                INSERT INTO transactions (user_id, amount, transaction_type, description)
                VALUES (?, ?, ?, ?)
            ''', (referrer_id, REFERRAL_BONUS, 'referral', f'Реферальный бонус за пользователя {user_id}'))
        
        conn.commit()
        
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        
        return dict(user)
    
    def _generate_referral_code(self, user_id: int) -> str:
        """Генерация уникального реферального кода"""
        hash_obj = hashlib.md5(str(user_id).encode())
        return hash_obj.hexdigest()[:8]
    
    def get_user_balance(self, user_id: int) -> float:
        """Получить баланс пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result['balance'] if result else 0.0
    
    def update_balance(self, user_id: int, amount: float, description: str = ''):
        """Обновить баланс пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?',
                      (amount, user_id))
        cursor.execute('''
            INSERT INTO transactions (user_id, amount, transaction_type, description)
            VALUES (?, ?, ?, ?)
        ''', (user_id, amount, 'balance_update', description))
        conn.commit()
        conn.close()
    
    def get_referral_stats(self, user_id: int) -> Dict[str, Any]:
        """Получить статистику рефералов"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) as count, COALESCE(SUM(bonus_paid), 0) as total_earned
            FROM referrals WHERE referrer_id = ?
        ''', (user_id,))
        stats = cursor.fetchone()
        
        cursor.execute('SELECT referral_code FROM users WHERE user_id = ?', (user_id,))
        code = cursor.fetchone()
        
        conn.close()
        
        return {
            'count': stats['count'] if stats else 0,
            'total_earned': stats['total_earned'] if stats else 0,
            'referral_code': code['referral_code'] if code else ''
        }
    
    def add_proxy(self, user_id: int, proxy_type: str, proxy_data: str, price: float):
        """Добавить прокси пользователю"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO proxies (user_id, proxy_type, proxy_data, price)
            VALUES (?, ?, ?, ?)
        ''', (user_id, proxy_type, proxy_data, price))
        conn.commit()
        conn.close()
    
    def get_user_proxies(self, user_id: int):
        """Получить все прокси пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM proxies 
            WHERE user_id = ? AND status = 'active'
            ORDER BY created_at DESC
        ''', (user_id,))
        proxies = cursor.fetchall()
        conn.close()
        return [dict(p) for p in proxies]
    
    def use_promocode(self, user_id: int, code: str) -> tuple[bool, str]:
        """Использовать промокод"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Проверяем, использовал ли пользователь этот код
        cursor.execute('''
            SELECT * FROM promocode_usage 
            WHERE user_id = ? AND code = ?
        ''', (user_id, code))
        
        if cursor.fetchone():
            conn.close()
            return False, "Вы уже использовали этот промокод"
        
        # Проверяем существование промокода
        cursor.execute('''
            SELECT * FROM promocodes 
            WHERE code = ? AND uses_left > 0
        ''', (code,))
        
        promo = cursor.fetchone()
        if not promo:
            conn.close()
            return False, "Промокод не найден или исчерпан"
        
        # Начисляем бонус
        amount = promo['amount']
        cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?',
                      (amount, user_id))
        cursor.execute('UPDATE promocodes SET uses_left = uses_left - 1 WHERE code = ?',
                      (code,))
        cursor.execute('''
            INSERT INTO promocode_usage (user_id, code, amount)
            VALUES (?, ?, ?)
        ''', (user_id, code, amount))
        cursor.execute('''
            INSERT INTO transactions (user_id, amount, transaction_type, description)
            VALUES (?, ?, ?, ?)
        ''', (user_id, amount, 'promocode', f'Промокод {code}'))
        
        conn.commit()
        conn.close()
        
        return True, f"Промокод активирован! На баланс начислено {amount}₽"


# Инициализация базы данных
db = Database()


class CryptoPayAPI:
    """Класс для работы с Crypto Bot API"""
    
    def __init__(self, token: str):
        self.token = token
        self.base_url = "https://pay.crypt.bot/api"
    
    def create_invoice(self, amount: float, description: str, user_id: int) -> Optional[Dict]:
        """Создать счет на оплату"""
        url = f"{self.base_url}/createInvoice"
        
        payload = {
            "asset": "USDT",  # или другая криптовалюта
            "amount": str(amount / 90),  # примерный курс рубль/USDT
            "description": description,
            "paid_btn_name": "callback",
            "paid_btn_url": f"https://t.me/your_bot?start=payment_{user_id}"
        }
        
        headers = {
            "Crypto-Pay-API-Token": self.token,
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.error(f"Error creating invoice: {e}")
        
        return None
    
    def check_invoice(self, invoice_id: int) -> Optional[Dict]:
        """Проверить статус счета"""
        url = f"{self.base_url}/getInvoices"
        
        headers = {
            "Crypto-Pay-API-Token": self.token
        }
        
        params = {
            "invoice_ids": invoice_id
        }
        
        try:
            response = requests.get(url, params=params, headers=headers)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.error(f"Error checking invoice: {e}")
        
        return None


crypto_api = CryptoPayAPI(CRYPTO_BOT_TOKEN)


# Клавиатуры
def get_main_menu_keyboard():
    """Главное меню"""
    keyboard = [
        [InlineKeyboardButton("🔗 Реферальная система", callback_data="referral")],
        [InlineKeyboardButton("👤 Профиль", callback_data="profile")],
        [InlineKeyboardButton("🛒 Купить прокси", callback_data="buy_proxy")],
        [InlineKeyboardButton("ℹ️ Информация", callback_data="info")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_profile_keyboard():
    """Клавиатура профиля"""
    keyboard = [
        [InlineKeyboardButton("🎁 Промокод", callback_data="promocode")],
        [InlineKeyboardButton("💰 Пополнить", callback_data="topup")],
        [InlineKeyboardButton("📦 Мои прокси", callback_data="my_proxies")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_proxy_types_keyboard():
    """Клавиатура выбора типа прокси"""
    keyboard = [
        [InlineKeyboardButton(f"FunTime - {PROXY_TYPES['funtime']['price']}₽", 
                            callback_data="proxy_funtime")],
        [InlineKeyboardButton(f"HolyWorld - {PROXY_TYPES['holyworld']['price']}₽", 
                            callback_data="proxy_holyworld")],
        [InlineKeyboardButton(f"SpokyTime - {PROXY_TYPES['spokytime']['price']}₽", 
                            callback_data="proxy_spokytime")],
        [InlineKeyboardButton(f"Любой сервер - {PROXY_TYPES['anyserver']['price']}₽", 
                            callback_data="proxy_anyserver")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_payment_methods_keyboard(proxy_type: str):
    """Клавиатура методов оплаты"""
    keyboard = [
        [InlineKeyboardButton("💎 Crypto Bot (Telegram)", 
                            callback_data=f"pay_crypto_{proxy_type}")],
        [InlineKeyboardButton("⭐ Telegram Stars", 
                            callback_data=f"pay_stars_{proxy_type}")],
        [InlineKeyboardButton("🎮 FunPay", 
                            callback_data=f"pay_funpay_{proxy_type}")],
        [InlineKeyboardButton("💳 СПБ/RU карта", 
                            callback_data=f"pay_card_{proxy_type}")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="buy_proxy")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_back_to_menu_keyboard():
    """Кнопка возврата в меню"""
    keyboard = [[InlineKeyboardButton("⬅️ Вернуться в меню", callback_data="main_menu")]]
    return InlineKeyboardMarkup(keyboard)


# Обработчики команд
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    
    # Проверяем реферальный код
    referrer_code = None
    if context.args and len(context.args) > 0:
        referrer_code = context.args[0]
    
    # Создаем или получаем пользователя
    db_user = db.get_or_create_user(
        user.id,
        user.username,
        user.first_name,
        user.last_name,
        referrer_code
    )
    
    welcome_text = f"""
👋 Добро пожаловать, {user.first_name}!

🎮 Это бот для покупки прокси для Minecraft серверов.
Обходите баны по IP с помощью наших прокси!

💰 Ваш баланс: {db_user['balance']:.2f}₽

Выберите действие:
"""
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=get_main_menu_keyboard()
    )


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий на кнопки"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    if data == "main_menu":
        await show_main_menu(query, user_id)
    
    elif data == "referral":
        await show_referral_system(query, user_id)
    
    elif data == "profile":
        await show_profile(query, user_id)
    
    elif data == "buy_proxy":
        await show_proxy_types(query)
    
    elif data == "info":
        await show_info(query)
    
    elif data.startswith("proxy_"):
        proxy_type = data.replace("proxy_", "")
        await show_payment_methods(query, proxy_type)
    
    elif data.startswith("pay_"):
        await handle_payment(query, data, user_id, context)
    
    elif data == "promocode":
        context.user_data['waiting_for'] = 'promocode'
        await query.edit_message_text(
            "🎁 Введите промокод:",
            reply_markup=get_back_to_menu_keyboard()
        )
    
    elif data == "topup":
        await show_topup_options(query)
    
    elif data == "my_proxies":
        await show_my_proxies(query, user_id)


async def show_main_menu(query, user_id: int):
    """Показать главное меню"""
    balance = db.get_user_balance(user_id)
    text = f"""
🏠 Главное меню

💰 Ваш баланс: {balance:.2f}₽

Выберите действие:
"""
    await query.edit_message_text(text, reply_markup=get_main_menu_keyboard())


async def show_referral_system(query, user_id: int):
    """Показать реферальную систему"""
    stats = db.get_referral_stats(user_id)
    bot_username = (await query.get_bot()).username
    
    referral_link = f"https://t.me/{bot_username}?start={stats['referral_code']}"
    
    text = f"""
🔗 Реферальная система

💰 Приглашайте друзей и получайте {REFERRAL_BONUS}₽ за каждого!

📊 Ваша статистика:
👥 Приглашено: {stats['count']} чел.
💵 Заработано: {stats['total_earned']:.2f}₽

🔗 Ваша реферальная ссылка:
{referral_link}

Отправьте эту ссылку друзьям, и когда они запустят бота, вы получите бонус!
"""
    await query.edit_message_text(text, reply_markup=get_back_to_menu_keyboard())


async def show_profile(query, user_id: int):
    """Показать профиль"""
    user = db.get_or_create_user(user_id)
    stats = db.get_referral_stats(user_id)
    proxies = db.get_user_proxies(user_id)
    
    text = f"""
👤 Ваш профиль

💰 Баланс: {user['balance']:.2f}₽
👥 Рефералов: {stats['count']}
📦 Активных прокси: {len(proxies)}

📊 Статистика:
💵 Заработано с рефералов: {stats['total_earned']:.2f}₽
"""
    await query.edit_message_text(text, reply_markup=get_profile_keyboard())


async def show_proxy_types(query):
    """Показать типы прокси"""
    text = """
🛒 Выберите тип прокси:

🎮 FunTime - 26₽
Прокси для сервера FunTime

🌍 HolyWorld - 36₽
Прокси для сервера HolyWorld

👻 SpokyTime - 20₽
Прокси для сервера SpokyTime

🌐 Любой сервер - 40₽
Универсальный прокси для любого сервера
"""
    await query.edit_message_text(text, reply_markup=get_proxy_types_keyboard())


async def show_payment_methods(query, proxy_type: str):
    """Показать методы оплаты"""
    proxy_info = PROXY_TYPES[proxy_type]
    text = f"""
💳 Выберите метод оплаты

Прокси: {proxy_info['name']}
Цена: {proxy_info['price']}₽
"""
    await query.edit_message_text(
        text,
        reply_markup=get_payment_methods_keyboard(proxy_type)
    )


async def handle_payment(query, data: str, user_id: int, context):
    """Обработка оплаты"""
    parts = data.split("_")
    payment_method = parts[1]
    proxy_type = parts[2]
    
    proxy_info = PROXY_TYPES[proxy_type]
    price = proxy_info['price']
    
    if payment_method == "crypto":
        # Создаем счет через Crypto Bot
        invoice = crypto_api.create_invoice(
            amount=price,
            description=f"Прокси {proxy_info['name']}",
            user_id=user_id
        )
        
        if invoice and invoice.get('ok'):
            pay_url = invoice['result'].get('pay_url', '')
            text = f"""
✅ Счет создан!

💎 Оплата через Crypto Bot

Прокси: {proxy_info['name']}
Цена: {price}₽

Нажмите на кнопку ниже для оплаты:
"""
            keyboard = [
                [InlineKeyboardButton("💳 Оплатить", url=pay_url)],
                [InlineKeyboardButton("⬅️ Назад", callback_data="buy_proxy")]
            ]
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await query.edit_message_text(
                "❌ Ошибка создания счета. Попробуйте позже.",
                reply_markup=get_back_to_menu_keyboard()
            )
    
    else:
        # Для остальных методов - показываем сообщение
        text = f"""
💳 Оплата: {proxy_info['name']} - {price}₽

Для оплаты через {'Telegram Stars' if payment_method == 'stars' else 'FunPay' if payment_method == 'funpay' else 'карту'}:

📱 Напишите администратору {ADMIN_USERNAME}

Сообщите ему:
- Что хотите купить: {proxy_info['name']}
- Сумма: {price}₽
- Метод оплаты: {'Telegram Stars' if payment_method == 'stars' else 'FunPay' if payment_method == 'funpay' else 'СПБ/RU карта'}

Администратор поможет вам с оплатой и выдаст прокси.
"""
        await query.edit_message_text(text, reply_markup=get_back_to_menu_keyboard())


async def show_topup_options(query):
    """Показать опции пополнения"""
    text = """
💰 Пополнение баланса

Выберите метод пополнения:
"""
    keyboard = [
        [InlineKeyboardButton("💎 Crypto Bot", callback_data="topup_crypto")],
        [InlineKeyboardButton("📱 Другие методы", callback_data="topup_manual")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="profile")]
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def show_my_proxies(query, user_id: int):
    """Показать прокси пользователя"""
    proxies = db.get_user_proxies(user_id)
    
    if not proxies:
        text = """
📦 Мои прокси

У вас пока нет активных прокси.
Купите прокси в разделе "Купить прокси"!
"""
    else:
        text = "📦 Ваши активные прокси:\n\n"
        for idx, proxy in enumerate(proxies, 1):
            text += f"{idx}. {PROXY_TYPES.get(proxy['proxy_type'], {}).get('name', 'Unknown')}\n"
            text += f"   Данные: {proxy['proxy_data']}\n"
            text += f"   Куплено: {proxy['created_at'][:10]}\n\n"
    
    await query.edit_message_text(text, reply_markup=get_back_to_menu_keyboard())


async def show_info(query):
    """Показать информацию"""
    text = """
ℹ️ Информация

🎮 О сервисе:
Мы предоставляем прокси для обхода IP-банов на серверах Minecraft.

🔒 Гарантии:
- Быстрые и стабильные прокси
- Работают на всех серверах
- Техническая поддержка 24/7

💡 Как это работает:
1. Выберите нужный тип прокси
2. Оплатите удобным способом
3. Получите данные для подключения
4. Подключитесь и играйте!

📱 Поддержка: {ADMIN_USERNAME}

🔗 Реферальная программа:
Приглашайте друзей и получайте 5₽ за каждого!
"""
    await query.edit_message_text(text, reply_markup=get_back_to_menu_keyboard())


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    user_id = update.effective_user.id
    text = update.message.text
    
    # Проверяем, ждем ли мы промокод
    if context.user_data.get('waiting_for') == 'promocode':
        success, message = db.use_promocode(user_id, text.strip())
        
        await update.message.reply_text(
            message,
            reply_markup=get_back_to_menu_keyboard()
        )
        
        context.user_data['waiting_for'] = None
    
    else:
        # Показываем главное меню
        balance = db.get_user_balance(user_id)
        await update.message.reply_text(
            f"💰 Ваш баланс: {balance:.2f}₽\n\nВыберите действие:",
            reply_markup=get_main_menu_keyboard()
        )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Update {update} caused error {context.error}")


def main():
    """Главная функция"""
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)
    
    # Запускаем бота
    logger.info("Bot started!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
