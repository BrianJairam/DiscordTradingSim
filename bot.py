import asyncio
import discord
import os
import schedule
import sqlite3
import random
import bank
import economy_functions as ef
import trading
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

client = commands.Bot(command_prefix = '$')

@client.event
async def on_ready():
    db = sqlite3.connect('main.sqlite')
    cursor = db.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS money(
            user_id TEXT,
            dollars REAL,
            PRIMARY KEY (user_id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ledger(
            transaction_id INTEGER PRIMARY KEY,
            transaction_type TEXT,
            guild_id TEXT,
            giver_id TEXT,
            receiver_id TEXT,
            dollars REAL,
            giver_balance REAL,
            receiver_balance REAL,
            date TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bank_deposits(
            user_id INTEGER PRIMARY KEY,
            dollars REAL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bank_loans(
            user_id INTEGER PRIMARY KEY,
            dollars REAL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stocks(
            user_id INTEGER,
            stock TEXT,
            amount INTEGER,
            PRIMARY KEY(user_id, stock)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stock_ledger(
            transaction_id INTEGER PRIMARY KEY,
            transaction_type TEXT,
            guild_id,
            user_id INTEGER,
            stock TEXT,
            stock_price REAL,
            number INTEGER,
            payment REAL,
            date TEXT
        )
    ''')

    print("DiscordTradingSim is ready.")

# General Commands 

# $version

@client.command()
async def version(ctx):
    await ctx.send('Alpha 1.0')

# $dice

@client.command()
async def dice(ctx, choice):
    faces = [1, 2, 3, 4, 5, 6]
    choice = int(choice)
    if (choice not in faces):
        await ctx.send('Please enter number from 1-6!')
    else:
        result = random.choice(faces)
        if (choice == result):
            ef.ledger_update("Gambling", ctx.guild.id, "\"Casino\"", ctx.message.author.id, 0.01)
            ef.money_transfer(ctx.message.author.id, 0.01)
            ef.money_transfer("\"Casino\"", -0.01)
            await ctx.send(f'Rolled a {result}. You win $0.01!')
        else:
            await ctx.send(f'Rolled a {result}. You lose!')

@client.command()
async def wagered_dice(ctx, choice, bet: float):
    faces = [1, 2, 3, 4, 5, 6]
    choice = int(choice)
    if (choice not in faces):
        await ctx.send('Please enter number from 1-6!')
    elif (bet <= 0):
        await ctx.send('Please enter a positive bet!')
    elif (ef.check_balance(ctx.message.author.id) < bet):
        await ctx.send('You don\'t have enough money!')
    else:
        result = random.choice(faces)
        if (choice == result):
            winnings = bet * 2
            ef.ledger_update("Gambling", ctx.guild.id, "\"Casino\"", ctx.message.author.id, winnings)
            ef.money_transfer(ctx.message.author.id, winnings)
            ef.money_transfer("\"Casino\"", -winnings)
            await ctx.send(f'Rolled a {result}. You win {winnings:.2f} dollars!')
        else:
            ef.ledger_update("Gambling", ctx.guild.id, ctx.message.author.id, "\"Casino\"", bet)
            ef.money_transfer(ctx.message.author.id, -bet)
            ef.money_transfer("\"Casino\"", bet)
            await ctx.send(f'Rolled a {result}. You lose {bet:.2f} dollars!')

@dice.error
async def info_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('Please enter a number from 1-6.')

# $iscliff

@client.command()
async def iscliff(ctx, *, member: discord.Member):
    if (member.name == 'CliffRouge'):
        await ctx.send('This guy is a bit of a chiller...')
    else:
        await ctx.send('Not chill, not chill!')

@iscliff.error
async def info_error(ctx, error):
    if isinstance(error, commands.BadArgument):
        await ctx.send('Thats like, not even a user on this server bro.')
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('Gimme a user and I can tell you if they are CliffRouge or not.')

# Economy Commands 

# $balance

@client.command()
async def balance(ctx):
    balance = ef.check_balance(ctx.message.author.id)
    await ctx.send(f'{ctx.message.author.name} has {"{:.2f}".format(round(balance, 2))} dollars.')


# $give

@client.command()
async def give(ctx, member: discord.Member, amount: float):
    amount = round(amount, 2)
    if (ctx.message.author.guild_permissions.administrator):
        ef.ledger_update("Test", ctx.guild.id, "\"Admin\"", member.id, amount)
        ef.money_transfer(member.id, amount)
        await ctx.send(f'Gave {"{:.2f}".format(round(amount, 2))} dollars to {member.name}.')
    else:
        await ctx.send(f'You must be an admin to do that.')

# $pay

@client.command()
async def pay(ctx, member: discord.Member, amount: float):
    amount = round(amount, 2)
    gbalance = ef.check_balance(ctx.message.author.id)
    if (amount <= 0): 
        await ctx.send(f'Please enter a positive amount!')
    elif (ctx.message.author.id == member.id):
        await ctx.send(f'You can\'t pay yourself!')
    elif (gbalance - amount < 0):
        await ctx.send(f'You do not have enough money!')
    else:
        ef.ledger_update("User_Transfer", ctx.guild.id, ctx.message.author.id, member.id, amount)
        ef.money_transfer(member.id, amount)
        ef.money_transfer(ctx.message.author.id, -amount)
        await ctx.send(f'{ctx.message.author.name} paid {member.name} {"{:.2f}".format(round(amount, 2))} dollars.')


# Bank Commands 

# $bank_balance

@client.command()
async def bank_balance(ctx):
    msg = bank.bank_balance(ctx.message.author)
    await ctx.send(msg)

# $deposit

@client.command()
async def deposit(ctx, amount: float):
    amount = round(amount, 2)
    msg = bank.new_deposit(ctx.message.author, amount, ctx.guild.id)
    await ctx.send(msg)


# $withdraw

@client.command()
async def withdraw(ctx, amount: float):
    amount = round(amount, 2)
    msg = bank.new_withdrawal(ctx.message.author, amount, ctx.guild.id)
    await ctx.send(msg)

# $withdraw

@client.command()
async def interest_rates(ctx):
    await ctx.send(f'The deposit rate at the bank is currently {bank.deposit_rate * 100}%. The lending rate at the bank is currently {bank.lending_rate * 100}%.')

# Bank Proccesses

# Check if interest needs to be paid out anytime a message is sent

@client.event
async def on_message(message):
    bank.handle_interest()
    await client.process_commands(message)

# Trading Commands

# $get_quote

@client.command()
async def get_quote(ctx, stock_name):
    msg = trading.get_quote(stock_name)
    await ctx.send(msg)

# $company_info

@client.command()
async def company_info(ctx, stock_name):
    msg = trading.company_info(stock_name)
    await ctx.send(msg)

# $buy

@client.command()
async def buy(ctx, stock_name, number:int):
    msg = trading.buy_stock(stock_name, number, ctx.message.author, ctx.guild.id)
    await ctx.send(msg)

# $portfolio
@client.command()
async def portfolio(ctx):
    embed = trading.check_portfolio(ctx.message.author, 1)
    await ctx.send(embed=embed)





client.run(TOKEN)
