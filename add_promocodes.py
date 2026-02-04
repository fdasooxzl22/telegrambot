#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для добавления промокодов в базу данных
"""

import sqlite3

def add_promocode(code: str, amount: float, uses_left: int = 100):
    """Добавить промокод в базу данных"""
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO promocodes (code, amount, uses_left)
            VALUES (?, ?, ?)
        ''', (code, amount, uses_left))
        conn.commit()
        print(f"✅ Промокод '{code}' добавлен: {amount}₽, {uses_left} использований")
    except sqlite3.IntegrityError:
        print(f"❌ Промокод '{code}' уже существует")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        conn.close()


def list_promocodes():
    """Показать все промокоды"""
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM promocodes')
    promocodes = cursor.fetchall()
    
    if not promocodes:
        print("📭 Промокодов нет")
    else:
        print("\n📋 Список промокодов:")
        print("-" * 60)
        for promo in promocodes:
            print(f"Код: {promo[1]:15} | Сумма: {promo[2]:6.2f}₽ | Осталось: {promo[3]:3} шт.")
    
    conn.close()


if __name__ == '__main__':
    print("🎁 Управление промокодами\n")
    
    # Примеры добавления промокодов
    add_promocode("START2024", 10.0, 1000)
    add_promocode("WELCOME", 25.0, 500)
    add_promocode("PROMO100", 100.0, 50)
    add_promocode("BONUS50", 50.0, 100)
    
    print("\n" + "=" * 60 + "\n")
    
    # Показать все промокоды
    list_promocodes()
