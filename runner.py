#!/usr/bin/env python3
import argparse
import asyncio
import json
import logging
import os
import time
import traceback
# from telethon import TelegramClient
# from telethon.tl import types#  * PeerUser, UserStatusOnline, UserStatusOffline, UserStatusRecently, UserStatusLastWeek, UserStatusLastMonth
from telethon.sync import TelegramClient, types
from telethon.tl.functions.users import GetFullUserRequest
import mysql.connector

# TODO
# make asynchronous

class Program:
	# async def scrapeall # TODO

	def scrape(self, uid):
		# uid	phone	username	first_name	last_name	bio	pfpcount	currentpfpid	sharingtime	timestamp
		user = self.client.get_entity(uid)
		full = self.client(GetFullUserRequest(user))
		photos = self.client.get_profile_photos(user)

		match type(user.status):
			case types.UserStatusOffline:
				status = 0
			case types.UserStatusOnline:
				status = 1
			case _:
				status = -1 # user is not sharing exact time. (UserStatusRecently, UserStatusLastWeek, UserStatusLastMonth)

		return [
			uid,
			user.phone,
			user.username,
			user.first_name,
			user.last_name,
			full.full_user.about,
			len(photos),
			photos[0].id,
			status != -1, # sharing time or not
			status == 1 # online or not
		]

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
		parser = argparse.ArgumentParser(description = "Main tstalk runner (adds activity and updates to db)")
		parser.add_argument("--dbcredentials", action = "store", type = str, default = "$TSTALKDBCREDS", help = "Env to load credentials from")
		parser.add_argument("--apicredentials", action = "store", type = str, default = "$TSTALKAPICREDS", help = "Env to load credentials from")
		parser.add_argument("--session", action = "store", type = str, default = "tstalk.session", help = "Session file location")
		parser.add_argument("--nologifnotimeshare", action = "store_true", help = "Do not log activity if user is not sharing exact time")
		parser.add_argument("-v", "--verbose", action = "store_true", dest = "verbose", help = "Print extra info (sql commands)")
		parser.add_argument("-n", "--nocommit", action = "store_true", dest = "nocommit", help = "No commit (dry-run)")
		self.args = parser.parse_args()

		logging.basicConfig(
			filename = os.path.join(directory := os.path.dirname(__file__), "scraper.log"), # log at directory file located
			filemode = "a",
			format = "Time: `%(asctime)s` Line: %(lineno)d %(message)s",
			datefmt = "%d/%m/%Y %H:%M:%S",
			level = logging.ERROR
		)
		self.logger = logging.getLogger("scraper.log")

		with open(os.path.expanduser(os.path.expandvars(self.args.apicredentials))) as fp:
			self.apicreds = json.load(fp)

		with open(os.path.expanduser(os.path.expandvars(self.args.dbcredentials))) as fp:
			credentials = json.load(fp)

		try:
			self.connection = mysql.connector.connect(
				host = credentials["host"],
				port = credentials["port"],
				user = credentials["username"],
				password = credentials["password"],
				database = credentials["database"],
				buffered = True
			)
			self.cursor = self.connection.cursor()

			# nigger loop
			loop = asyncio.new_event_loop()
			asyncio.set_event_loop(loop)

			self.client = TelegramClient(self.args.session, self.apicreds["api_id"], self.apicreds["api_hash"])
			self.client.start()
			self.client.get_dialogs() # get users you have chatted / added contact with into this context

			t = round(time.time())
			r = self.sql("SELECT * FROM `users`")

			if r == []:
				print("No users to scrape. add them with manager.py")

			for uid in r:
				uid = uid[0]
				user = self.scrape(uid)

				if (user[8] or self.args.nologifnotimeshare) and user[9]: # log them as online at this timestamp if they are online and they are sharing time

					self.sql("INSERT INTO `activity` (uid, timestamp) VALUES (%s, %s)", (uid, t))
				# elif not user[8]:
				# 	self.sql("INSERT INTO `activity` (uid, timestamp) VALUES (%s, %s)", (uid, -1)) #

				latestProfile = list(self.sql("SELECT * FROM `updates` WHERE uid = %s ORDER BY `timestamp` DESC LIMIT 1", [uid]))

				if latestProfile != []:
					latestProfile = list(latestProfile[0][:9])

				user = user[:9]
				user[8] = int(user[8])

				# print(latestProfile)
				# print(user)
				# print(list(type(i) for i in latestProfile))
				# print(list(type(i) for i in user))
				# print(list(j == latestProfile[i] for i, j in enumerate(user)))
				# input(user == latestProfile)

				if latestProfile == [] or user != latestProfile: # if the table is empty
					self.sql("INSERT INTO `updates` (`uid`, `phone`, `username`, `first`, `last`, `bio`, `pfpcount`, `currentpfpid`, `sharingtime`, `timestamp`) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", (*user, t))
		except Exception as exception:
			traceback.print_exc()
			self.logger.error(f"Undefined error: {exception}")

if __name__ == "__main__":
	Program()
