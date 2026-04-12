# T-Stalk
Simplistic program to monitor telegram user activity (online time and profile updates).

## Install / Setup
clone repo `https://github.com/Repository42/tstalk.git`

create an app at `my.telegram.org`

put `api_id` and `api_hash` into `api_creds.json`

install requirements: `python -m pip -r requirements.txt`

setup the database and the database user using `tstalk_schema.sql`

add the script runner.py to cron (this will be changed to systemd timers in the future to allow for more frequent updates)

after you have added script to cron you can check everything is running by checking logs for errors with `cat scraper.log` if there are errors it will show in the file

## Usage

### runner.py

add user activity to database.

### manager.py

add or remove users from program.

modes: `add`, `remove`, `list`

phone:    `python manager.py add +44123123123`

username: `python manager.py add @example`

id:       `python manager.py add 123123123`

or if you dont want the user to be logged in your bash history you can do `python manager.py {mode}` and you will be prompted for the user 

if the identifier is not valid the script will raise an error.

### viewer.py

generate graphs from data.

### owner.py 

prints information about owner of .session file, so you can verify you are logged in as the correct user.
