#!/usr/bin/env python3
import argparse
import json
import os
from datetime import datetime
from random import *
import mysql.connector

def sql(statement, values = ()):
	if not args.silent: # print queries so we can see if we have fucked up the SQL
		stmt = statement.replace("%s", "{}")
		if values != ():
			stmt = stmt.format(*values)
		print(stmt)

	cursor.execute(statement, (*values,))

	if not args.nocommit:
		connection.commit()
	return cursor.fetchall()

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description = "Create random dataset for testing purposes")
	parser.add_argument("dbcredentials", action = "store", type = str, default = "$TSTALKDBCREDS")
	parser.add_argument("--nodrop", action = "store_true", help = "Do not drop db")
	parser.add_argument("--users", action = "store", type = tuple, default = (10, 20), help = "Range for the amount of users to create")
	parser.add_argument("--arows", action = "store", type = tuple, default = (750, 1000), help = "Range for the amount of `activity` rows to create")
	parser.add_argument("--urows", action = "store", type = tuple, default = (20, 30), help = "Range for the amount of `update` rows to create")
	parser.add_argument("--time", action = "store", type = tuple, default = ("2026/4/1",), help = "Date range")
	parser.add_argument("-s", "--silent", action = "store_true", dest = "silent", help = "Do not print anything (sql commands)")
	parser.add_argument("-n", "--nocommit", action = "store_true", dest = "nocommit", help = "No commit (dry-run)")
	parser.add_argument("-k", "--keep", action = "store_true", dest = "keep", help = "Do not clear db")
	args = parser.parse_args()

	if input(
		f"This script will create a random data set, please make the supplied credentials file `{args.dbcredentials}` is correct as this will mess up a live database if ran. [`y` or `yes` to continue]: "
		).lower() not in ["y", "yes"]:
		exit()

	with open(os.path.expanduser(os.path.expandvars(args.dbcredentials))) as fp:
		credentials = json.load(fp)

	connection = mysql.connector.connect(
		host = credentials["host"],
		port = credentials["port"],
		user = credentials["username"],
		password = credentials["password"],
		database = credentials["database"],
		buffered = True
	)
	cursor = connection.cursor()

	if not args.keep:
		cursor.execute("DELETE FROM `activity`")
		cursor.execute("DELETE FROM `updates`")
		cursor.execute("DELETE FROM `users`")

	ltime = int(datetime.strptime(args.time[0], "%Y/%m/%d").timestamp())
	rtime = int((datetime.strptime(args.time[1], "%Y/%m/%d") if len(args.time) > 1 else datetime.now()).timestamp())
	# dates = choice(ltime, rtime)
	print(ltime, rtime)

	users = tuple((
		randint(1_000_000_000, 9_999_999_999),
		randint(ltime, int(ltime + (rtime - ltime) / 2.5))
		) for i in range(choice(args.users))
	)

	for uid, timestamp in users: # insert fake users
		sql("INSERT INTO `users` (uid) VALUES (%s)", (uid,))

	for uid, timestamp in choices(users, k = randint(*args.urows)):
		user = (
			uid,
			"FakePhone" if choices((0, 1), (35, 65))[0] == 0 else None,
			f"FakeUsername_{randint(1, 1000)}" if choices((0, 1), (35, 65))[0] == 0 else None,
			"Fake First Name", # if choices((0, 1), (35, 65))[0] == 0 else None,
			"Fake Last Name" if choices((0, 1), (35, 65))[0] == 0 else None,
			"Fake Bio" if choices((0, 1), (35, 65))[0] == 0 else None,
			randint(0, 30),# if choices((0, 1), (35, 65))[0] == 0 else None,
			randint(1_000_000_000_000_000_000, 8_999_999_999_999_999_999),
			choices((0, 1), (20, 80))[0],
			randint(timestamp, int(timestamp + (rtime - timestamp) / 2.5)),
		)
		sql("INSERT INTO `updates` (`uid`, `phone`, `username`, `first`, `last`, `bio`, `pfpcount`, `currentpfpid`, `sharingtime`, `timestamp`) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", user)

	for uid, timestamp in choices(users, k = randint(*args.arows)):
		sql("INSERT INTO `activity` (uid, timestamp) VALUES (%s, %s)", (uid, randint(timestamp, int(timestamp + (rtime - timestamp) / 2.5))))
