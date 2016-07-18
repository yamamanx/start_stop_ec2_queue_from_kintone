# coding:utf-8

from apiclient.discovery import build

API_KEY = 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
CALENDAR_ID = 'ja.japanese#holiday@group.v.calendar.google.com'

def getHolidays():

    try:
        service = build(serviceName='calendar', version='v3', developerKey=API_KEY)
        events = service.events().list(calendarId=CALENDAR_ID).execute()

        holidays = []
        for item in sorted(events['items'], key=lambda item: item['start']['date']):
            holidays.append(item['start']['date'])

        return holidays

    except Exception as e:
        return e
