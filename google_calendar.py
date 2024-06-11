

import datetime
import os.path
import json 
import base64

from zoneinfo import ZoneInfo

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar"]


# Setting this to True will print verbose information of each event
DEBUG = False

# Setting this to True avoid actual interaction with Google Apis 
DRY_RUN = False

# Send notifications 
# 'all', 'externalOnly', 'none'
# see: https://developers.google.com/calendar/api/v3/reference/events/insert
SEND_UPDATES = 'all'

recipients = json.load(open('attendees.json', 'r'))

# -------------------------------
# Configuration To Be EDITED
# -------------------------------

# This prefix will be used in any event 
# Apart from the summary, it is also used to calculate the event id
# for this reason cannot be changed, unless you want events to be duplicated
prefix = "TBC - "


# Configure the iterations parameter: 
# - start date of all the iterations
# - number of iterations ( i.e. sprints)
# - duration of each iteration expressend in week ( 1 week == 5 working days )
config_start_date           = datetime.date(2024, 6, 17)
config_num_of_sprints       = 6
config_sprint_duration      = 1


calendar_id = 'primary'

config_time_zone = "Europe/Rome"

config_planning_start_time  = datetime.time(hour=10, minute=0)
config_planning_duration    = datetime.timedelta(minutes=60)
config_planning_summary     = "{prefix} Sprint #{sprint_num} - Planning"

config_daily_start_time     = datetime.time(hour=10, minute=0)
config_daily_duration       = datetime.timedelta(minutes=15)
config_daily_summary        = "{prefix} Sprint #{sprint_num} - Standup Meeting"

config_review_start_time    = datetime.time(hour=15, minute=0)
config_review_duration      = datetime.timedelta(minutes=60)
config_review_summary       = "{prefix} Sprint #{sprint_num} - Review"

config_retro_start_time     = datetime.time(hour=16, minute=0)
config_retro_duration       = datetime.timedelta(minutes=60)
config_retro_summary        = "{prefix} Sprint #{sprint_num} - Retrospective"







def get_credentials():
  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          "credentials.json", SCOPES
      )
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
      token.write(creds.to_json())

  return creds


def get_service():
  return build("calendar", "v3", credentials=get_credentials())




# CRUD
def list_events(q=''):

  events_result = (
      get_service().events()
      .list(
          calendarId=calendar_id,
          timeMin=datetime.datetime.now(datetime.UTC).isoformat(),
          maxResults=50,
          singleEvents=True,
          orderBy="startTime",
          q=prefix,
      )
      .execute()
  )
  return events_result.get("items", [])

def get_event(event_id):
  return get_service().events().get(calendarId=calendar_id, eventId=event_id).execute()


def delete_event(event):
  return get_service().events().delete(calendarId=calendar_id, eventId=event['id'], sendUpdates=SEND_UPDATES).execute()


def create_event(event):
  return get_service().events().insert(calendarId=calendar_id, body=event, sendUpdates=SEND_UPDATES).execute()


def update_event(event):
  return get_service().events().update(calendarId=calendar_id, eventId=event['id'], body=event, sendUpdates=SEND_UPDATES).execute()


def upsert_event(event):
    try:
      fe = get_event(event['id'])
      update_event(event)
    except Exception as ex:
      create_event(event)

def delete_all(events):
  for e in events:
    delete_event(e)

def upsert_all(events):
  for e in events:
    upsert_event(e)




# Factory Method
def build_event(description, date, start_time, duration, repeat=1, attendees=None, variant=None):
  timezone = ZoneInfo(config_time_zone)

  start = datetime.datetime.combine(date, start_time)
  end = start + duration

  event_id = base64.b32hexencode(bytearray(description+str(variant), 'utf-8')).decode('utf-8').lower().rstrip('=')
  event = {
    'id': event_id,
    'summary': description,
    'start': {
      'dateTime': start.isoformat(),
      'timeZone': config_time_zone,
    },
    'end': {
      'dateTime': end.isoformat(),
      'timeZone':  config_time_zone,
    },
    'attendees': attendees
  }

  if repeat > 1:
    event['recurrence'] = [
      f'RRULE:FREQ=DAILY;COUNT={repeat}'
    ]

  return event




# Logic
def create_all_sprints(start_date, num_of_sprints=6, sprint_duration=1):
  print(f"Creating {num_of_sprints} sprints of {sprint_duration} weeks each")

  assert sprint_duration >= 1
  assert start_date.isoweekday() == 1
  
  for i in range(1, num_of_sprints + 1):
    sprint_start_date = start_date + datetime.timedelta(days=(i - 1) * (sprint_duration * 7))
    print(f"- {i} Creating sprint starting in {sprint_start_date}")
    create_sprint_events(sprint_start_date, i, sprint_duration)
    


def create_sprint_events(start_date, sprint_num, sprint_duration):
  
  # Calculate days
  days = (sprint_duration - 1) * 7 + 5 - 1 

  last_day = start_date + datetime.timedelta(days=days)

  def format_summary(template):
    return template.format(prefix=prefix, sprint_num=sprint_num)

  events = [
    build_event(
      description=format_summary(config_planning_summary), 
      date=start_date, 
      start_time=config_planning_start_time, 
      duration=config_planning_duration, 
      attendees=recipients['team_members'] + recipients['po']
    ),
    build_event(
      description=format_summary(config_review_summary), 
      date=last_day, 
      start_time=config_review_start_time, 
      duration=config_review_duration,
      attendees=recipients['team_members'] + recipients['po']
    ),
    build_event(
      description=format_summary(config_retro_summary),
      date=last_day, 
      start_time=config_review_start_time, 
      duration=config_review_duration,
      attendees=recipients['team_members']
    ),
  ]

  for w in range(0, sprint_duration):
    
    start_date + datetime.timedelta(days=7 * w)
    repeat = 4 if w == 0 else 5

    events.append(
      build_event(
        description=format_summary(config_daily_summary), 
        date=start_date + datetime.timedelta(days=1), 
        start_time=config_daily_start_time, 
        duration=config_daily_duration,
        repeat=repeat,
        variant=w, # use the week progressive to generate the event.id 
        attendees=recipients['team_members']
      )
    )

  if DEBUG:
    print_events(events)
  
  if not DRY_RUN:
    upsert_all(events)


def print_events(events):
  for e in events:
    print(f"{e['start']['dateTime']} {e['summary']} {'recurrence' in e} {e['id']} {e['attendees']}")



if __name__ == "__main__":
  create_all_sprints(start_date=config_start_date, num_of_sprints=config_num_of_sprints, sprint_duration=config_sprint_duration)
