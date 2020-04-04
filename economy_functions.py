import sqlite3
import datetime

def check_balance(member_id):
    db = sqlite3.connect('main.sqlite')
    cursor = db.cursor()
    cursor.execute('SELECT dollars FROM money WHERE user_id = ?', (member_id,))
    result = cursor.fetchone()
    if result is None:
        sql = ("INSERT INTO money (user_id, dollars) VALUES(?, ?)")
        val = (member_id, 0)
        cursor.execute(sql, val)
        db.commit()
        ans = 0
    else:
        ans = round(result[0], 2)
    cursor.close()
    db.close()
    return ans

def money_transfer(member_id, amount): 
    db = sqlite3.connect('main.sqlite')
    cursor = db.cursor()
    cursor.execute('SELECT dollars FROM money WHERE user_id = ?', (member_id,))
    result = cursor.fetchone()
    if result is None:
        sql = ("INSERT INTO money (user_id, dollars) VALUES(?, ?)")
        val = (member_id, amount)
    else:
        current_balance = result[0]
        sql = ("UPDATE money SET dollars = ? WHERE user_id = ?")
        val = (current_balance + amount, member_id)
    cursor.execute(sql, val)
    db.commit()
    cursor.close()
    db.close()

def ledger_update(transaction_type, guild_id, giver_id, receiver_id, payment):
    db = sqlite3.connect('main.sqlite')
    gbalance = check_balance(giver_id)
    rbalance = check_balance(receiver_id)
    gbalance -= payment
    rbalance += payment
    db = sqlite3.connect('main.sqlite')
    cursor = db.cursor()
    ledger_sql = ("INSERT INTO ledger (transaction_type, guild_id, giver_id, receiver_id, dollars, giver_balance, receiver_balance, date) VALUES (?, ?, ?, ?, ?, ?, ?, ?)")
    ledger_val = (transaction_type, guild_id, giver_id, receiver_id, payment, gbalance, rbalance, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    cursor.execute(ledger_sql, ledger_val)
    db.commit()
    cursor.close()
    db.close()





