#!/usr/bin/env python3
#DESCRIPTION: manage users
import argparse
import asyncio
import json
import os
from telethon.sync import TelegramClient, types
from telethon.tl.functions.users import GetFullUserRequest
import mysql.connector

class Program:
	def sql(self, statement, values = []):
		if self.args.verbose: # print queries so we can see if we have fucked up the SQL
			stmt = statement.replace("%s", "{}")

			if values != []:
				stmt = stmt.format(*values)
			print(stmt)

		self.cursor.execute(statement, [*values])

		if not self.args.nocommit:
			self.connection.commit()
		return self.cursor.fetchall()

	def __init__(self):
		parser = argparse.ArgumentParser(description = "Add and remove users from tstalk")
		parser.add_argument("arguments", help = "Arguments, first arg should be `mode` (add or remove) followed by user identifier", nargs = "+")
		parser.add_argument("--dbcredentials", action = "store", type = str, default = "$TSTALKDBCREDS", help = "Env to load credentials from")
		parser.add_argument("--apicredentials", action = "store", type = str, default = "$TSTALKAPICREDS", help = "Env to load credentials from")
		parser.add_argument("--session", action = "store", type = str, default = "tstalk.session", help = "Session file location")
		parser.add_argument("-v", "--verbose", action = "store_true", dest = "verbose", help = "Print extra info (sql commands)")
		parser.add_argument("-n", "--nocommit", action = "store_true", dest = "nocommit", help = "No commit (dry-run)")
		self.args = parser.parse_args()

		with open(os.path.expanduser(os.path.expandvars(self.args.apicredentials))) as fp:
			self.apicreds = json.load(fp)

		with open(os.path.expanduser(os.path.expandvars(self.args.dbcredentials))) as fp:
			credentials = json.load(fp)

		self.connection = mysql.connector.connect(
			host = credentials["host"],
			port = credentials["port"],
			user = credentials["username"],
			password = credentials["password"],
			database = credentials["database"],
			buffered = True
		)
		self.cursor = self.connection.cursor()

		loop = asyncio.new_event_loop() # nigger loop
		asyncio.set_event_loop(loop)

		self.client = TelegramClient(self.args.session, self.apicreds["api_id"], self.apicreds["api_hash"])
		self.client.start()
		self.client.get_dialogs() # get users from account, if phone number is provided for added contact will resolve it to uid

		uid = self.client.get_entity(entry := (self.args.arguments[1] if len(self.args.arguments) > 1 else input("Input identifier: "))).id
		print(f"Resolved: {entry} -> {uid}")

		match self.args.arguments[0]:
			case "add":
				print(f"Adding: `{uid}` to T-Stalk")
				self.sql("INSERT IGNORE INTO `users` (`uid`) VALUES (%s)", [uid])
				# add last seen data if present
				# TODO alert operator if they are sharing time or not.
			case "remove":
				print(f"Removing: `{uid}` from T-Stalk (this wont remove entries from database)")
				self.sql("DELETE FROM `users` WHERE uid = %s", [uid])
			case _:
				print(f"Unknown command: `{self.args.arguments[0]}`")

if __name__ == "__main__":
	Program()
