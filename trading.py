import asyncio
import datetime
import discord
import math
import os
import schedule
import time
import pandas as pd
import numpy as np
import yfinance as yf
import iexfinance
import sqlite3
import bank
import economy_functions as ef
from dotenv import load_dotenv
from pandas_datareader import data as pdr

brokerage_fee = 10.00

def add_to_portfolio(user_id, stock_name, amount):
    stock = "\"" + stock_name + "\""
    db = sqlite3.connect('main.sqlite')
    cursor = db.cursor()
    cursor.execute('SELECT amount FROM stocks WHERE user_id = ? AND stock = ?', (user_id, stock))
    result = cursor.fetchone()
    if result is None:
        sql = ("INSERT INTO stocks (user_id, stock, amount) VALUES(?, ?, ?)")
        val = (user_id, stock, amount)
    else:
        current_amount = result[0]
        sql = ("UPDATE stocks SET amount = ? WHERE user_id = ? AND stock = ?")
        val = (current_amount + amount, user_id, stock)
    cursor.execute(sql, val)
    db.commit()
    cursor.close()
    db.close()

def stock_ledger_update(transaction_type, guild_id, user_id, stock_name, stock_price, number):
    stock_name = stock_name.upper()
    db = sqlite3.connect('main.sqlite')
    cursor = db.cursor()
    ledger_sql = ("INSERT INTO stock_ledger (transaction_type, guild_id, user_id, stock, stock_price, number, payment, date) VALUES (?, ?, ?, ?, ?, ?, ?, datetime(\'now\'))")
    ledger_val = (transaction_type, guild_id, user_id, "\"" + stock_name + "\"", stock_price, number, stock_price * number)
    cursor.execute(ledger_sql, ledger_val)
    db.commit()
    cursor.close()
    db.close()

def company_info(stock_name):
    stock_name = stock_name.upper()
    company = yf.Ticker(stock_name)
    info = company.info
    msg = f"""**Company Name:** {info['longName']} \n
        **Sector:** {info['sector']} \n
        **Industry:** {info['industry']} \n
        **Country**: {info['country']} \n
        **Website**: {info['website']} \n
        **Summary**: {info['longBusinessSummary'][:1500] + "..."}
        """
    return msg

def get_quote(stock_name):
    stock_name = stock_name.upper()
    data = yf.download(tickers = stock_name, period = "1d", interval = "2m", auto_adjust = True, prepost = True)
    if (data.empty):
        msg = f"No results found for {stock_name}. Are you sure you have the right symbol?"
    else:
        quote = round(data.tail(1)["Close"].values[0], 2)
        msg = f"The current quote for {stock_name} is {quote:.2f} dollars."
    return msg
    

def buy_stock(stock_name, number, user, guild_id):
    # Error Checking
    stock_name = stock_name.upper()
    data = yf.download(tickers = stock_name, period = "1d", interval = "2m", auto_adjust = True, prepost = True)
    if (data.empty):
        msg = f"No results found for {stock_name}. Are you sure you have the right symbol?"
        return msg
    # Get quote and payment
    quote = data.tail(1)["Close"].values[0]
    payment = quote * number
    total_owed = payment + brokerage_fee
    # Check if user had funds
    bal = ef.check_balance(user.id)
    if (bal < total_owed):
        if (bal > 10):
            number_max = math.floor((bal - 10) / quote)
            msg = f"You do not have the required funds to buy {number} shares of {stock_name}! The maximum number of shares you can afford is {number_max}..."
        else :
            msg = f"You do not have the required funds to buy {number} shares of {stock_name}! You have less than {brokerage_fee:.2f} dollars, the brokerage fee."
        return msg
    # Update stock ledger
    stock_ledger_update("\"Buy Order\"", guild_id, user.id, stock_name, quote, number)
    # Update ledger
    ef.ledger_update("\"Buy Stock\"", guild_id, user.id, "\"Brokerage\"", total_owed)
    ef.money_transfer(user.id, -total_owed)
    ef.money_transfer("\"Brokerage\"", brokerage_fee)
    add_to_portfolio(user.id, stock_name, number)
    msg = f"{user.name} bought {number} shares of {stock_name} at {quote:.2f} dollars each. The total value of the transaction was {payment:.2f} dollars, plus the {brokerage_fee:.2f} dollar brokerage fee."
    return msg


def check_portfolio(user, slide):
    db = sqlite3.connect('main.sqlite')
    cursor = db.cursor()
    cursor.execute('SELECT stock, amount FROM stocks WHERE user_id = ? ORDER BY amount DESC' , (user.id,))
    rows = cursor.fetchall()
    table = []
    for row in rows:
        stock_name = row[0][1:-1]
        amount = row[1]
        data = yf.download(tickers = stock_name, period = "1d", interval = "2m", auto_adjust = True, prepost = True)
        price = round(data.tail(1)["Close"].values[0], 2)
        value = round(price * amount, 2)
        table.append((value, price, amount, stock_name))
    table.sort(reverse=True)
    total_value = 0
    embed=discord.Embed(title=f"Portfolio of {user.name}", description="Shares | Price Per Share | Total Value", color=0x00fa00)
    embed.set_thumbnail(url= user.avatar_url)
    for row in table:
        stock_name = row[3]
        amount = row[2]
        price = row[1]
        value = row[0]
        total_value += value
        embed.add_field(name=stock_name, value=f"{amount} | {price:.2f} | {value:.2f}", inline=True)
    embed.set_footer(text=f"The total value of your portfolio is {total_value:.2f} dollars!")
    return embed





    
    
    





