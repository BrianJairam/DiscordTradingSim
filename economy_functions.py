import sqlite3

def check_balance(member_id):
    db = sqlite3.connect('main.sqlite')
    cursor = db.cursor()
    cursor.execute(f"SELECT dollars FROM money WHERE user_id = {member_id}")
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
    cursor.execute(f"SELECT dollars FROM money WHERE user_id = {member_id}")
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
