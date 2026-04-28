#!/usr/bin/env python3
# only partially vibe coded
import argparse
import asyncio
import json
import logging
import os
import time
import traceback
import aiomysql
from telethon import TelegramClient, types
from telethon.tl.functions.users import GetFullUserRequest

class Program:
	async def sql(self, conn, statement, values = []):
		values = values or []
		if self.args.verbose:
			stmt = statement.replace("%s", "{}")
			if values != []:
				stmt = stmt.format(*values)
			print(stmt)

		async with conn.cursor() as cursor:
			await cursor.execute(statement, values)
			if not self.args.nocommit:
				await conn.commit()
			try:
				return await cursor.fetchall()
			except:
				return []

	async def scrape(self, uid):
		try:
			user = await self.client.get_entity(uid)
			full = await self.client(GetFullUserRequest(user))
			photos = await self.client.get_profile_photos(user)

			match type(user.status):
				case types.UserStatusOffline:
					status = 0
				case types.UserStatusOnline:
					status = 1
				case _:
					status = -1

			return [
				uid,
				user.phone,
				user.username,
				user.first_name,
				user.last_name,
				full.full_user.about,
				len(photos),
				photos[0].id if photos else None,
				status != -1, # sharing time
				status == 1   # online
			]
		except Exception as e:
			self.logger.error(f"Scrape error for {uid}: {e}")
			return None

	async def process_user(self, pool, uid, timestamp):
		async with pool.acquire() as conn:
			user = await self.scrape(uid)
			if not user:
				return

			# Log activity if online and sharing time (or override flag set)
			if (user[8] or not self.args.nologifnotimeshare) and user[9]:
				await self.sql(conn, "INSERT INTO `activity` (uid, timestamp) VALUES (%s, %s)", (uid, timestamp))

			latestProfile = await self.sql(conn, "SELECT * FROM `updates` WHERE uid = %s ORDER BY `timestamp` DESC LIMIT 1", [uid]) # Fetch latest profile in db
			user = user[:9]
			user[8] = int(user[8]) # Convert bool to int for DB comparison

			doUpdate = False

			if not latestProfile:
				doUpdate = True
			else:
				latestProfile = list(latestProfile[0][:9])
				if user != latestProfile:
					doUpdate = True

			# print(latestProfile)
			# print(user)
			# print(list(type(i) for i in latestProfile))
			# print(list(type(i) for i in user))
			# print(list(j == latestProfile[i] for i, j in enumerate(user)))
			# input(user == latestProfile)

			if doUpdate:
				await self.sql(
					conn,
					"INSERT INTO `updates` (`uid`, `phone`, `username`, `first`, `last`, `bio`, `pfpcount`, `currentpfpid`, `sharingtime`, `timestamp`) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
					(*user, timestamp)
				)

	async def start(self):
		try:
			with open(os.path.expanduser(os.path.expandvars(self.args.apicredentials))) as fp:
				self.apicreds = json.load(fp)

			with open(os.path.expanduser(os.path.expandvars(self.args.dbcredentials))) as fp:
				credentials = json.load(fp)

			async with aiomysql.create_pool(
				host = credentials["host"],
				port = credentials.get("port", 3306),
				user = credentials["username"],
				password = credentials["password"],
				db = credentials["database"],
				autocommit = True
			) as pool:

				self.client = TelegramClient(self.args.session, self.apicreds["api_id"], self.apicreds["api_hash"])
				await self.client.start()
				await self.client.get_dialogs()

				timestamp = round(time.time())

				async with pool.acquire() as conn:
					r = await self.sql(conn, "SELECT uid FROM `users`")

				if not r:
					print("No users to scrape. Add them with manager.py")
					return

				# Run processing for all users concurrently
				tasks = [self.process_user(pool, row[0], timestamp) for row in r]
				await asyncio.gather(*tasks)
		except Exception as exception:
			traceback.print_exc()
			self.logger.error(f"Undefined error: {exception}")
		finally:
			if hasattr(self, 'client'):
				await self.client.disconnect()

	def __init__(self):
		parser = argparse.ArgumentParser(description = "Main tstalk runner")
		parser.add_argument("--dbcredentials", action = "store", type = str, default = "$TSTALKDBCREDS")
		parser.add_argument("--apicredentials", action = "store", type = str, default = "$TSTALKAPICREDS")
		parser.add_argument("--session", action = "store", type = str, default = "tstalk.session")
		parser.add_argument("--nologifnotimeshare", action = "store_true")
		parser.add_argument("-v", "--verbose", action = "store_true", dest = "verbose")
		parser.add_argument("-n", "--nocommit", action = "store_true", dest = "nocommit")
		self.args = parser.parse_args()

		logging.basicConfig(
			filename = os.path.join(os.path.dirname(__file__), "scraper.log"),
			filemode = "a",
			format = "Time: `%(asctime)s` Line: %(lineno)d %(message)s",
			datefmt = "%d/%m/%Y %H:%M:%S",
			level = logging.ERROR
		)
		self.logger = logging.getLogger("scraper.log")

if __name__ == "__main__":
	program = Program()
	asyncio.run(program.start())
