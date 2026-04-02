# T-Stalk
Simplistic program to monitor telegram user activity (online time and profile updates).

## Install / Setup
create an app at `my.telegram.org`

put `api_id` and `api_hash` into `api_creds.json`

install requirements: `python -m pip -r requirements.txt`

setup the database and the database user using `tstalk_schema.sql`

add the script runner.py to cron (this will be changed in the future to allow for more frequent updates)

after you have added

## Usage

### runner.py

add user activity to database.



### manager.py

add or remove users from program.

modes: `add` or `remove`

phone:    `python manager.py add +44123123123`

username: `python manager.py add @example`

id:       `python manager.py add 123123123`

if the identifier is not valid the script will raise an error.

### viewer.py

generate graphs from data.
