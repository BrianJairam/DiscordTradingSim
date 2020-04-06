import asyncio
import datetime
import discord
import math
import os
import schedule
import time
import pandas as pd
import numpy as np
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import math
import yfinance as yf
import iexfinance
import sqlite3
import bank
import economy_functions as ef
from dotenv import load_dotenv
from pandas_datareader import data as pdr
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()

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
    ledger_sql = ("INSERT INTO stock_ledger (transaction_type, guild_id, user_id, stock, stock_price, number, payment, date) VALUES (?, ?, ?, ?, ?, ?, ?, ?)")
    ledger_val = (transaction_type, guild_id, user_id, "\"" + stock_name + "\"", stock_price, number, stock_price * number, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
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
    if number <= 0:
        msg = "Please enter a positive amount!"
        return msg
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
    ef.ledger_update("Buy_Stock", guild_id, user.id, "\"Brokerage\"", total_owed)
    ef.money_transfer(user.id, -total_owed)
    ef.money_transfer("\"Brokerage\"", brokerage_fee)
    add_to_portfolio(user.id, stock_name, number)
    msg = f"{user.name} bought {number} shares of {stock_name} at {quote:.2f} dollars each. The total value of the transaction was {payment:.2f} dollars, plus the {brokerage_fee:.2f} dollar brokerage fee."
    return msg

def sell_stock(stock_name, number, user, guild_id):
    newstock_name = "\"" + stock_name + "\""
    # Sell All feature
    if (number == "all" or number == "All" or number == "ALL"):
        db = sqlite3.connect('main.sqlite')
        cursor = db.cursor()
        cursor.execute('SELECT amount FROM stocks WHERE user_id = ? AND stock = ?' , (user.id, newstock_name))
        result = cursor.fetchone()
        if (result is None):
            msg = f"You have no shares of {stock_name}!"
            return msg
        else:
            number = result[0]
    # Make sure number is an int
    number = int(number) 
    stock_name = stock_name.upper()
    # Error Checking
    data = yf.download(tickers = stock_name, period = "1d", interval = "2m", auto_adjust = True, prepost = True)
    if (data.empty):
        msg = f"No results found for {stock_name}. Are you sure you have the right symbol?"
        return msg
    # Get quote
    quote = data.tail(1)["Close"].values[0]
    payment = round(quote * number, 2)
    total_owed = payment - brokerage_fee
    # Check if user has enough stock to sell
    db = sqlite3.connect('main.sqlite')
    cursor = db.cursor()
    cursor.execute('SELECT amount FROM stocks WHERE user_id = ? AND stock = ?' , (user.id, newstock_name))
    result = cursor.fetchone()
    if (result is None):
        msg = f"You have no shares of {stock_name}!"
        return msg
    current_number = result[0]
    if (number > current_number):
        msg = f"You only have {current_number} shares of {stock_name}!"
        return msg
    # Update portfolio
    elif (number == current_number):
        sql = ("DELETE FROM stocks WHERE user_id = ? AND stock = ?")
        val = (user.id, newstock_name)
    else:
        sql = ("UPDATE stocks SET amount = ? WHERE user_id = ? AND stock = ?")
        val = (current_number - number, user.id, newstock_name)
    cursor.execute(sql, val)
    db.commit()
    cursor.close()
    db.close()
    # Update stock ledger
    stock_ledger_update("\"Sell Order\"", guild_id, user.id, stock_name, quote, number)
    # Update ledger
    ef.ledger_update("Sell_Stock", guild_id,"\"Brokerage\"", user.id, total_owed)
    ef.money_transfer(user.id, total_owed)
    ef.money_transfer("\"Brokerage\"", brokerage_fee)
    msg = f"{user.name} sold {number} shares of {stock_name} at {quote:.2f} dollars each. The total value of the transaction was {payment:.2f} dollars, minus the {brokerage_fee:.2f} dollar brokerage fee."
    return msg


def check_portfolio(user):
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

def buy_history(user):
    db = sqlite3.connect('main.sqlite')
    cursor = db.cursor()
    cursor.execute('SELECT * FROM stock_ledger WHERE user_id = ? AND transaction_type = \"\"\"Buy Order\"\"\"' , (user.id,))
    rows = cursor.fetchall()
    embed=discord.Embed(title=f"Buy Orders of {user.name}", description="Shares | Price Per Share | Total Value | Date", color=0x00fa00)
    embed.set_thumbnail(url= user.avatar_url)
    for row in rows:
        stock_name = row[4][1:-1]
        amount = row[6]
        price = row[5]
        value = row[7]
        date = row[8]
        embed.add_field(name=stock_name, value=f"{amount} | {price:.2f} | {value:.2f} | {date}" , inline=False)
    embed.set_footer(text=f"Buy Orders")
    return embed

def sell_history(user):
    db = sqlite3.connect('main.sqlite')
    cursor = db.cursor()
    cursor.execute('SELECT * FROM stock_ledger WHERE user_id = ? AND transaction_type = \"\"\"Sell Order\"\"\"' , (user.id,))
    rows = cursor.fetchall()
    embed=discord.Embed(title=f"Sell Orders of {user.name}", description="Shares | Price Per Share | Total Value | Date", color=0x00fa00)
    embed.set_thumbnail(url= user.avatar_url)
    for row in rows:
        stock_name = row[4][1:-1]
        amount = row[6]
        price = row[5]
        value = row[7]
        date = row[8]
        embed.add_field(name=stock_name, value=f"{amount} | {price:.2f} | {value:.2f} | {date}" , inline=False)
    embed.set_footer(text=f"Sell Orders")
    return embed

def order_history(user):
    db = sqlite3.connect('main.sqlite')
    cursor = db.cursor()
    cursor.execute('SELECT * FROM stock_ledger WHERE user_id = ?', (user.id,))
    rows = cursor.fetchall()
    embed=discord.Embed(title=f"Orders of {user.name}", description="Shares | Price Per Share | Total Value | Date", color=0x00fa00)
    embed.set_thumbnail(url= user.avatar_url)
    for row in rows:
        if (row[1] == "\"Buy Order\""):
            order_type = "BUY "
        else:
            order_type = "SELL "
        stock_name = row[4][1:-1]
        amount = row[6]
        price = row[5]
        value = row[7]
        date = row[8]
        embed.add_field(name= order_type + stock_name, value=f"{amount} | {price:.2f} | {value:.2f} | {date}" , inline=False)
    embed.set_footer(text=f"Sell Orders")
    return embed

def portfolio_history(user, start, inc):
    inc = "1d"
    db = sqlite3.connect('main.sqlite')
    cursor = db.cursor()
    cursor.execute('SELECT * FROM stock_ledger WHERE user_id = ?', (user.id,))
    ledger_data = cursor.fetchall()
    if (ledger_data == None):
        return "User has no portfolio!"
    if (start == "begin"):
        start = datetime.datetime.strptime(ledger_data[0][8], '%Y-%m-%d %H:%M:%S').date()
    stock_history = []
    histories = []
    end = datetime.date.today()
    if (end.weekday() >= 5):
        end -= datetime.timedelta(days= end.weekday() - 4)
    if (start.weekday() >= 5):
        start -= datetime.timedelta(days= start.weekday() - 4)
    # Produce a dictionary that holds all historical stock data
    for row in ledger_data:
        stock = row[4][1:-1]
        if (stock not in stock_history):
            start_date = start.strftime("%Y-%m-%d")
            end_date = end.strftime("%Y-%m-%d")
            print(stock)
            print(start_date)
            print(end_date)
            print(inc)
            yf_stock_data = yf.download(stock, start=start_date, end=end_date, interval=inc)
            stock_history.append(stock)
            histories.append(yf_stock_data)
    # Set some variables to track elements of value over time
    cumulative_buysell = 0
    stocks = {}
    i = 0
    max_i = len(ledger_data) - 1
    dates = []
    values = []
    cur_date = start
    # Loop through dates, calculting value of portfolio at any given date (upto but not including the end date)
    while (cur_date < end):
        if (i <= max_i):
            while (datetime.datetime.strptime(ledger_data[i][8], '%Y-%m-%d %H:%M:%S').date() <= cur_date):
                if (ledger_data[i][1] == "\"Buy Order\""):
                    cumulative_buysell -= ledger_data[i][7]
                    stock = ledger_data[i][4][1 : -1]
                    number = ledger_data[i][6]
                    if stock not in stocks:
                        stocks[stock] = number
                    else:
                        stocks[stock] += number
                elif (ledger_data[i][1] == "\"Sell Order\""):
                    cumulative_buysell += ledger_data[i][7]
                    stock = ledger_data[i][4][1 : -1]
                    number = ledger_data[i][6]
                    stocks[stock] -= number
                i += 1
                if (i > max_i):
                    break
        value = cumulative_buysell
        for stock in stocks:
            number = stocks[stock]
            for j in range(len(stock_history)):
                if (stock_history[j] == stock):
                    break
            last_date = cur_date
            while (last_date.strftime("%Y-%m-%d") not in histories[j]["Close"]):
                last_date -= datetime.timedelta(days=1)
            value += histories[j]["Close"][last_date.strftime("%Y-%m-%d")] * number
        dates.append(cur_date)
        values.append(round(value, 2))
        cur_date += datetime.timedelta(days=1)
    df = pd.DataFrame()
    df["Date"] = dates
    df["Value"] = values
    print(df)
    df_abs = df[["Value"]].applymap(lambda x: abs(x))
    m = df_abs["Value"].max()

    # Graph
    interval = math.ceil(len(dates) / 30) 
    plt.xlabel("Date")
    plt.ylabel("Gain/Loss ($)")
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=interval))
    plt.plot(dates,values)
    plt.gcf().autofmt_xdate()
    plt.ylim(-1.25 * m, 1.25 * m)
    plt.gca().grid(linestyle='-', linewidth='0.5', color='white')
    plt.gca().set_facecolor('#e5e5e5')
    plt.gca().get_lines()[0].set_color("#3b7dd8")
    plt.title(f"Net Gain/Loss of {user.name}\'s Portfolio Over Time")
    plt.savefig('Graphs/graph.png')
    plt.close(fig=None)
    return "Graph made"




    
    

