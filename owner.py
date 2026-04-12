import argparse
import asyncio
import json
import os
from telethon.sync import TelegramClient

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description = "Get info about .session file owner (make sure you are using correct account)")
	parser.add_argument("--apicredentials", action = "store", type = str, default = "$TSTALKAPICREDS", help = "Env to load credentials from")
	parser.add_argument("--session", action = "store", type = str, default = "tstalk.session", help = "Session file location")
	args = parser.parse_args()

	# kike loop
	loop = asyncio.new_event_loop()
	asyncio.set_event_loop(loop)

	with open(os.path.expanduser(os.path.expandvars(args.apicredentials))) as fp:
		apicreds = json.load(fp)

	with TelegramClient(args.session, apicreds["api_id"], apicreds["api_hash"]) as client:
		# "me" is a special keyword in Telethon for the session owner
		me = client.get_entity("me")

		print(f"--- Owner Profile ---")
		print(f"User ID: {me.id}")
		print(f"Phone: +{me.phone}")
		print(f"Username: @{me.username if me.username else 'None'}")
		print(f"Display Name: {me.first_name} {me.last_name or ''}")
