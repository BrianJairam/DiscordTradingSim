import asyncio
import datetime
import discord
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

def stock_ledger_update(transaction_type, guild_id, user_id, stock_name, stock_price, amount):
    stock_name = stock_name.upper()
    db = sqlite3.connect('main.sqlite')
    cursor = db.cursor()
    ledger_sql = ("INSERT INTO ledger (transaction_type, guild_id, giver_id, receiver_id, dollars, giver_balance, receiver_balance, date) VALUES (?, ?, ?, ?, ?, ?, ?, datetime(\'now\'))")
    # ledger_val = (transaction_type, guild_id, giver_id, receiver_id, payment, gbalance, rbalance)
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
        quote = data.tail(1)["Close"].values[0]
        msg = f"The current quote for {stock_name} is {quote} dollars."
    return msg
    

def buy_stock(stock_name, amount, user_id, guild_id):
    stock_name = stock_name.upper()
    data = yf.download(tickers = stock_name, period = "1d", interval = "2m", auto_adjust = True, prepost = True)
    if (data.empty):
        msg = f"No results found for {stock_name}. Are you sure you have the right symbol?"
        return msg
    quote = data.tail(1)["Close"].values[0]


    
    
    





