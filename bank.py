import asyncio
import datetime
import discord
import os
import schedule
import sqlite3
import time

import economy_functions as ef

from dotenv import load_dotenv

DEPOSIT_RATE = 0.01
LENDING_RATE = 0.02


def bank_balance(user):
    db = sqlite3.connect('main.sqlite')
    cursor = db.cursor()
    cursor.execute('SELECT dollars FROM bank_deposits WHERE user_id = ?',
                   (user.id,))
    result = cursor.fetchone()
    if result is None:
        sql = ("INSERT INTO bank_deposits (user_id, dollars) VALUES(?, ?)")
        val = (user.id, 0)
        cursor.execute(sql, val)
        db.commit()
        ans = 0
    else:
        ans = round(result[0], 2)
    cursor.close()
    db.close()
    return f'{user.name} has {ans:.2f} dollars in deposits.'


def new_deposit(user, amount, guild_id):
    if (amount <= 0):
        return "Please enter a positive amount."
    elif (ef.check_balance(user.id) < amount):
        return "You do not have enough money on you."
    else:
        db = sqlite3.connect('main.sqlite')
        cursor = db.cursor()
        cursor.execute('SELECT dollars FROM bank_deposits WHERE user_id = ?',
                       (user.id,))
        result = cursor.fetchone()
        if result is None:
            sql = ("INSERT INTO bank_deposits (user_id, dollars) VALUES(?, ?)")
            val = (user.id, amount)
        else:
            current_balance = result[0]
            sql = ("UPDATE bank_deposits SET dollars = ? WHERE user_id = ?")
            val = (current_balance + amount, user.id)
    cursor.execute(sql, val)
    db.commit()
    cursor.close()
    db.close()
    ef.ledger_update("Bank_Deposit", guild_id, user.id, "\"Bank\"", amount)
    ef.money_transfer("\"Bank\"", amount)
    ef.money_transfer(user.id, -amount)
    return f"{user.name} deposited {amount:.2f} dollars."


def new_withdrawal(user, amount, guild_id):
    if (amount <= 0):
        return "Please enter a positive amount."
    else:
        db = sqlite3.connect('main.sqlite')
        cursor = db.cursor()
        cursor.execute('SELECT dollars FROM bank_deposits WHERE user_id = ?',
                       (user.id,))
        result = cursor.fetchone()
        if (result is None or result[0] < amount):
            cursor.close()
            db.close()
            return "You do not have enough money in your account."
        else:
            current_balance = result[0]
            sql = ("UPDATE bank_deposits SET dollars = ? WHERE user_id = ?")
            val = (current_balance - amount, user.id)
            cursor.execute(sql, val)
            db.commit()
            cursor.close()
            db.close()
            ef.ledger_update("Bank_Withdrawal", guild_id,
                             "\"Bank\"", user.id, amount)
            ef.money_transfer(user.id, amount)
            ef.money_transfer("\"Bank\"", -amount)
            return f"{user.name} has withdrawn {amount:.2f} dollars."


def handle_interest():
    with open("date.txt", "r") as f:
        current_day = datetime.datetime.strptime(f.readline(),
                                                 '%m/%d/%Y').date()
        if (datetime.date.today() != current_day):
            d = (datetime.date.today() - current_day).days
            print(f"Paying interest for {d} days")
            db = sqlite3.connect('main.sqlite')
            cursor = db.cursor()
            cursor.execute(f'UPDATE bank_deposits SET dollars = \
                             dollars * {(1 + DEPOSIT_RATE / 365) ** d}')
            db.commit()
            with open("date.txt", "w+") as f:
                f.write(datetime.date.today().strftime('%m/%d/%Y'))
