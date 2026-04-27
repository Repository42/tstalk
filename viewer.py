#!/usr/bin/env python3
import argparse
import datetime
import json
import os
import matplotlib.pyplot as plt
import mysql.connector
import pandas
# TODO saferer, make it like manager.py where vars can be supplied with input()

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description = "Run premade commands")
	parser.add_argument("args", nargs = "+", help = "Command and arguments to give to program")
	parser.add_argument("--limit", action = "store", type = int, help = "Limit results by count")
	parser.add_argument("--ltime", action = "store", help = "Limit by time >= (unix timestamp or YYYY-MM-DDTHH:MM:SSZ)") # %Y-%m-%dT%H:%M:%SZ
	parser.add_argument("--rtime", action = "store", help = "Limit by time <= (unix timestamp or YYYY-MM-DDTHH:MM:SSZ)") # %Y-%m-%dT%H:%M:%SZ
	parser.add_argument("--commands", action = "store", type = str, default = "commands.json", help = "JSON file with commands")
	parser.add_argument("--save", action = "store", type = str, help = "Location to save file too, wont show gui")
	parser.add_argument("--dbcredentials", action = "store", type = str, default = "$TSTALKDBCREDS", help = "Env to load credentials from")
	# parser.add_argument("--silent", action = "store_true", help = "Dont print anything")
	args = parser.parse_args()

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
	convertTime = lambda time : int(time) if time.isdigit() else round(datetime.datetime.strptime(time, "%Y-%m-%dT%H:%M:%SZ").timestamp())

	with open(args.commands) as fp:
		allCommands = json.load(fp)

	key = args.args[0]
	showHelp = False

	if key not in (keys := allCommands.keys()):
		print(f"Unknown command: `{key}`")
		showHelp = True

	if key == "help":
		showHelp = True

	if showHelp:
		print("Available commands:")
		mKey = max(len(key) for key in keys)
		types = ['bar chart', 'scatter plot', 'broken barh', 'line plot', 'help']

		for key in keys:
			print(f"  {key} {(mKey - len(key)) * ' '} num args: {allCommands[key]['args']}  type: {types[allCommands[key]['mode']]}")

		exit()

	command = allCommands[key]
	arguments = args.args[1:]

	if (argCount := len(arguments)) != command["args"]: # check right amount of args
		print(f"Expected {command['args']} arguments recieved {argCount} arguments")
		exit()
		#TODO make it so that if incorrect args recieved or no args, ask for those values via input() like in manager.py
		# arguments = [input(f"Input value for argument-{arg}: ") for arg in range(argCount)]
		# then figure out what type its supposed to be or something ? maybe not cause its only ever going to be user id

	formattedCommands = [] # array of formatted sql commands to execute and plot data against

	for c in command["commands"]: # format commands
		# TODO fix ltime limit ? maybe not because thats snca and u can adjust with the gui
		if args.ltime is not None:
			ltime = convertTime(args.ltime)
			c += f"{' AND' if 'WHERE' in c else ' WHERE'} timestamp >= {ltime}"

		if args.rtime is not None:
			rtime = convertTime(args.rtime)
			c += f"{' AND' if 'WHERE' in c else ' WHERE'} timestamp <= {rtime}"

		# c += " ORDER BY timestamp ASC" # TODO only add in if not added in

		if args.limit is not None:
			c += f" LIMIT {args.limit}"
		formattedCommands.append(c)

	formattedCommands = "\t".join(formattedCommands).format(*arguments).split("\t") # idc this is unsafe it works and also its ur database
	colours = (
		(
			"skyblue",
			"lightcoral",
			"springgreen",
			"gold",
			"magenta",
			"orangered",
			"darkcyan"
		),
		(
			"navy",
			"darkred",
			"forestgreen"
		)
	)
	fig, ax = plt.subplots()
	allRes = []

	for index, c in enumerate(formattedCommands): # execute commands
		print(f"Executing: {c}")
		cursor.execute(c)
		r = cursor.fetchall()

		if len(r) == 0:
			print("No data!")
			exit()

		match len(r[0]):
			case 2:
				allRes.append((
					list(datetime.datetime.fromtimestamp(i[0]) for i in r),
					list(i[1] for i in r)
				))
			case 1:
				allRes.append((
					list(datetime.datetime.fromtimestamp(i[0]) for i in r)
				))
			case 0:
				print("No data!")
				exit()
			case _:
				print("erhhhasudaisduas")
				exit()

	match command["mode"]:
		case 0: # bar
			for index, result in enumerate(allRes):
				ax.bar(
					[datetime.timedelta(seconds = command["delta"] * index) + t for t in result[0]],
					# this and setting the delta to something smaller makes the lines "sit" next to eachother instead of overlapping,
					# could be helpful for comparing online times of two or more accounts
					result[1],
					width = datetime.timedelta(seconds = command["delta"]), # set width based on time because it doesnt do it automatically (retard line)
					color = colours[0][index],
					edgecolor = colours[1][index]
				)
		case 1: # scatter
			ax.plot(
				allRes[0], # date
				[eval(f"{i.hour}.{round((i.minute / 60) * 100)}") for i in allRes[0]], # minute
				linestyle = "None",
				marker = "o",
				color = colours[0][0]
			)
			plt.grid(True)
			# TODO do a loop here or something except i dont want to >:(
		case 2: # barh
			ax.broken_barh
			...
		case 3: # line
			print("Nah")
			exit()

	fig.autofmt_xdate()
	ax.xaxis_date()
	ax.set_xlabel(command["labels"][0], fontsize = 14)
	ax.set_ylabel(command["labels"][1], fontsize = 12)
	plt.title(command["title"].format(*arguments))
	plt.show()
