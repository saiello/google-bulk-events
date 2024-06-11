
# Bulk Calendar Events 

A simple script to setup recurring events of different iterations (scrum sprints). 


## Setup your env

Clone this repo

```
git clone https://github.com/saiello/google-bulk-events.git
cd google-bulk-events
```

Install all required dependencies

```
virtualenv .env 
source .venv/bin/activate 
pip install -r requirements.txt
```

Follow the instructions to enable Google Calendar api: https://developers.google.com/calendar/api/quickstart/python


## How to send scrum events

**1. Prepare recipent lists**

Create an `attendees.json` file in the working directory, containing different kind of users

``` 
{
    "team_members": [
        {"email": "dev-1@email.com"}, 
        {"email": "dev-2@email.com"}, 
        ...
    ], 
    "po": [
        {"email": "product-owner@email.com"}
        {"email": "stakeholder@email.com", "optional": true}
    ], 
    "others": []
}
```

**2. Define a prefix for all events**


Change the prefix that will be used in front of every events' summaries.

```
prefix = "<YOUR_PREFIX> - "
``` 

Apart from the summary, it is also used to calculate the event id and 
for this reason cannot be changed, unless you want events to be duplicated.


**3. Define scrum iterations**

Tweak the following variables to define iterations start date, repetitions and duration of each iteration.

```
config_start_date           = datetime.date(2024, 6, 17)
config_num_of_sprints       = 6
config_sprint_duration      = 1
```

**4. Run the script**

``` 
python google_calendar.py
``` 

## Additional info

**Dry run & Debug mode**

```
DEBUG = False

DRY_RUN = False
```

**Recommendations**

Start small, then scale up. 
Start by setting up all the events with a small number of user (only you), using an empty `attendees.json` file. 

```
{
    "team_members": [], 
    "po": [], 
    "others": []
}
```

Then if everything looks good add the others.


## TODO 

- [ ] refactor of code (i.e. event generator, GoogleApi resource, Cli)
- [ ] add a better user interface ( cli )
- [ ] allow for more flexible iterations configuration ( configure structure and repetition of iterations through a descriptor i.e. yaml)
- [ ] add further action (?) i.e. list, delete, check participants