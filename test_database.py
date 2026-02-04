#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестовый скрипт для проверки функциональности базы данных
Не требует установки telegram библиотеки
"""

import sqlite3
import hashlib
from datetime import datetime

REFERRAL_BONUS = 5.0

class DatabaseTest:
    """Тестовая версия класса Database"""
    
    def __init__(self, db_name='test_bot.db'):
        self.db_name = db_name
        self.init_db()
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
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
        
        conn.commit()
        conn.close()
    
    def _generate_referral_code(self, user_id):
        hash_obj = hashlib.md5(str(user_id).encode())
        return hash_obj.hexdigest()[:8]
    
    def get_or_create_user(self, user_id, username=None, first_name=None, 
                          last_name=None, referrer_code=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = cursor.fetchone()
        
        if user:
            conn.close()
            return dict(user)
        
        referral_code = self._generate_referral_code(user_id)
        referrer_id = None
        
        if referrer_code:
            cursor.execute('SELECT user_id FROM users WHERE referral_code = ?', 
                         (referrer_code,))
            referrer = cursor.fetchone()
            if referrer:
                referrer_id = referrer['user_id']
        
        cursor.execute('''
            INSERT INTO users (user_id, username, first_name, last_name, 
                             referral_code, referrer_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, username, first_name, last_name, referral_code, referrer_id))
        
        if referrer_id:
            cursor.execute(
                'UPDATE users SET balance = balance + ? WHERE user_id = ?',
                (REFERRAL_BONUS, referrer_id)
            )
            cursor.execute('''
                INSERT INTO referrals (referrer_id, referred_id, bonus_paid)
                VALUES (?, ?, ?)
            ''', (referrer_id, user_id, REFERRAL_BONUS))
            cursor.execute('''
                INSERT INTO transactions (user_id, amount, transaction_type, description)
                VALUES (?, ?, ?, ?)
            ''', (referrer_id, REFERRAL_BONUS, 'referral', 
                 f'Реферальный бонус за пользователя {user_id}'))
        
        conn.commit()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        
        return dict(user)
    
    def get_referral_stats(self, user_id):
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
    
    def get_user_balance(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result['balance'] if result else 0.0


def run_tests():
    """Запустить тесты"""
    print("="*60)
    print("🧪 Тестирование функциональности базы данных")
    print("="*60)
    
    db = DatabaseTest('test_bot.db')
    
    print("\n1️⃣ Тест: Создание пользователя")
    print("-"*60)
    user1 = db.get_or_create_user(
        user_id=100001,
        username="alice",
        first_name="Alice",
        last_name="Smith"
    )
    print(f"✅ Пользователь создан:")
    print(f"   ID: {user1['user_id']}")
    print(f"   Username: @{user1['username']}")
    print(f"   Имя: {user1['first_name']} {user1['last_name']}")
    print(f"   Баланс: {user1['balance']:.2f}₽")
    print(f"   Реферальный код: {user1['referral_code']}")
    
    print("\n2️⃣ Тест: Реферальная система")
    print("-"*60)
    stats1 = db.get_referral_stats(100001)
    print(f"Статистика до приглашения:")
    print(f"   Рефералов: {stats1['count']}")
    print(f"   Заработано: {stats1['total_earned']:.2f}₽")
    
    print(f"\n👉 Создаем реферала с кодом: {stats1['referral_code']}")
    user2 = db.get_or_create_user(
        user_id=100002,
        username="bob",
        first_name="Bob",
        last_name="Johnson",
        referrer_code=stats1['referral_code']
    )
    print(f"✅ Реферал создан: @{user2['username']}")
    
    balance1 = db.get_user_balance(100001)
    stats1_after = db.get_referral_stats(100001)
    print(f"\nСтатистика после приглашения:")
    print(f"   Баланс: {balance1:.2f}₽ (было: 0.00₽)")
    print(f"   Рефералов: {stats1_after['count']}")
    print(f"   Заработано: {stats1_after['total_earned']:.2f}₽")
    
    if balance1 == REFERRAL_BONUS and stats1_after['count'] == 1:
        print("✅ Реферальный бонус начислен правильно!")
    else:
        print("❌ Ошибка в начислении бонуса!")
    
    print("\n3️⃣ Тест: Множественные рефералы")
    print("-"*60)
    for i in range(3, 6):
        user = db.get_or_create_user(
            user_id=100000 + i,
            username=f"user{i}",
            first_name=f"User{i}",
            referrer_code=stats1['referral_code']
        )
        print(f"✅ Реферал #{i-1} создан: @{user['username']}")
    
    balance_final = db.get_user_balance(100001)
    stats_final = db.get_referral_stats(100001)
    print(f"\nИтоговая статистика:")
    print(f"   Баланс: {balance_final:.2f}₽")
    print(f"   Рефералов: {stats_final['count']}")
    print(f"   Заработано: {stats_final['total_earned']:.2f}₽")
    
    expected_balance = REFERRAL_BONUS * 4  # 4 реферала
    if balance_final == expected_balance and stats_final['count'] == 4:
        print("✅ Все рефералы обработаны правильно!")
    else:
        print(f"❌ Ошибка! Ожидалось {expected_balance}₽ и 4 реферала")
    
    print("\n4️⃣ Тест: Повторное получение пользователя")
    print("-"*60)
    user1_again = db.get_or_create_user(100001)
    if user1_again['user_id'] == user1['user_id']:
        print("✅ Повторное получение работает корректно")
    else:
        print("❌ Ошибка при повторном получении")
    
    print("\n" + "="*60)
    print("🎉 Все тесты завершены!")
    print("="*60)
    
    # Cleanup
    import os
    try:
        os.remove('test_bot.db')
        print("\n🧹 Тестовая база данных удалена")
    except:
        pass


if __name__ == '__main__':
    run_tests()
