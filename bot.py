import discord
import os
import sqlite3
import random
import economy_functions as ef
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
            ef.money_transfer(ctx.message.author.id, 0.01)
            await ctx.send(f'Rolled a {result}. You win $0.01!')
        else:
            await ctx.send(f'Rolled a {result}. You lose!')

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
    if (ctx.message.author.guild_permissions.administrator):
        ef.ledger_update("Test", ctx.guild.id, "\"Admin\"", member.id, amount)
        amount = round(amount, 2)
        ef.money_transfer(member.id, amount)
        await ctx.send(f'Gave {"{:.2f}".format(round(amount, 2))} dollars to {member.name}.')
    else:
        await ctx.send(f'You must be an admin to do that.')

# $pay

@client.command()
async def pay(ctx, member: discord.Member, amount: float):
    amount = round(amount, 2)
    gbalance = ef.check_balance(ctx.message.author.id)
    if (gbalance - amount < 0):
        await ctx.send(f'You do not have enough money!')
    else:
        ef.ledger_update("User_Transfer", ctx.guild.id, ctx.message.author.id, member.id, amount)
        ef.money_transfer(member.id, amount)
        ef.money_transfer(ctx.message.author.id, -amount)
        await ctx.send(f'{ctx.message.author.name} paid {member.name} {"{:.2f}".format(round(amount, 2))} dollars.')

    

        






client.run(TOKEN)
