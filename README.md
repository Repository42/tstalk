# T-Stalk
Simplistic program to monitor telegram user activity (online time and profile updates).

## Install / Setup
clone repo `https://github.com/Repository42/tstalk.git`

create an app at `my.telegram.org`

put `api_id` and `api_hash` into `api_creds.json`

install requirements: `python -m pip -r requirements.txt`

setup the database and the database user using `tstalk_schema.sql`

add the following variables to `.bashrc`

```bash
export TSTALKDBCREDS="~/tstalk/db_creds.json"
export TSTALKAPICREDS="~/tstalk/api_creds.json"
```

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

# Example commands: 

get help for commands: `python viewer.py help`

will output something like: 
```
Available commands are: 
  activitydaily        num args: 1
  activityhourly       num args: 1
  twoactivitydaily     num args: 2
  twoactivityhourly    num args: 2
  threeactivitydaily   num args: 3
  threeactivityhourly  num args: 3
  activityscatter      num args: 1
  profileupdates       num args: 1
  pfpupdates           num args: 1
  sharingtime          num args: 1
  activityline         num args: 1
  help                 num args: 0
```

bar chart for a user: `python viewer.py activitydaily {uidhere}`

bar chart for two users: `python viewer.py twoactivitydaily {firstuidhere} {seconduidhere}`

bar chart for three users: `python viewer.py twoactivitydaily {firstuidhere} {seconduidhere} {thirduidhere}`

user profile updates: `python viewer.py profileupdates {uidhere}`

### owner.py 

prints information about owner of .session file, so you can verify you are logged in as the correct user.

example of output:

```
--- Owner Profile ---
User ID: 1234567890
Phone: +123123123
Username: @telegram
Display Name: example
```
