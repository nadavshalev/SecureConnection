import sqlite3

from sqlite3 import Error


def sql_conn():
	try:
		con = sqlite3.connect('mydb.db')
		return con
	except Error:
		print(Error)


def sql_table(con):
	curs = con.cursor()
	curs.execute('''CREATE TABLE users(
							addr		text 	PRIMARY KEY,
							user_hash 	text	NOT NULL,
							server_hash	text	NOT NULL)''')
	con.commit()

def sql_insert(con, addr, user, server):
	curs = con.cursor()
	curs.execute("INSERT INTO users VALUES(?,?,?)", (addr, user, server))
	con.commit()

con = sql_conn()
# sql_table(con)
sql_insert(con, 'nadsav', 'aaa', 'bbb')
# sql_insert(con, 'shalev', 'ccc', 'ddd')

# curs = con.cursor()
# curs.execute('SELECT rowid,* FROM users ')
# for row in curs:
# 	print(row)


curs = con.cursor()
curs.execute('SELECT * FROM users WHERE addr=?', ('nadav',))
for row in curs:
	print(row)
