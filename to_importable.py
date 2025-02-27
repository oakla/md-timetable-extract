# from ics import Calendar, Event
from datetime import datetime
import csv
import re
import pandas as pd

from typing import Literal
# Predefined set of strings type
TimetableField = Literal[
    'week', 'day', 'date', 'event', 'start_time', 'end_time', 
    'location', 'session_type', 'subject', 'presenter'
]

import conf

# Predefined set of strings
WEEK = 'week'
DAY = 'day'
DATE = 'date'
DESCRIPTION = 'description'
START_TIME = 'start_time'
END_TIME = 'end_time'
LOCATION = 'location'
SESSION_TYPE = 'session_type'
SUBJECT = 'subject'
PRESENTER = 'presenter'


"Subject"
"Start Date"
"Start Time"
"End Date"
"End Time"
"All Day Event"
"Description"
"Location"
"Private"


class EventRow:

    def __init__(self, row:pd.Series):

        self.row = row

        self.subject = self.scrape_subject()
        self.session_type = row[SESSION_TYPE]

        self.name = self.make_name(row)
        self.start_date = self.start_date()
        self.start_time = self.start_time()
        self.end_date = self.end_date()
        self.end_time = self.end_time()
        self.all_day_event = not bool(self.start_time)  
        self.location = row[LOCATION]
        self.presenter = self.scrape_presenter()
        self.description = self.scrape_description()


    def scrape_subject(self):
        self.subject = self.row[SUBJECT]
        if self.subject:
            return self.subject
        
        match = re.search(r'(\w+):', self.row[DESCRIPTION])
        if match:
            return match.group(1)
        else:
            return None


    def make_name(self, row:pd.Series):
        return f'{self.subject} - {self.session_type}'


    def __str__(self):
        return f'{self.name} - {self.start_date} {self.start_time} - {self.end_time} - {self.location} - {self.presenter} - {self.description}'


    def scrape_presenter(self):
        if self.row[PRESENTER]:
            return self.row[PRESENTER]
        # find two letters betwen paranthesis
        match = re.search(r'\((\w{2})\)', self.row[DESCRIPTION])
        if match:
            return match.group(1)
        else:
            return None
    
    def scrape_description(self):
        event_text = self.row[DESCRIPTION]
        # remove newline characters and double spaces
        event_text = re.sub(r'\s+', ' ', event_text)
        
        match = re.search(r'\w+:\s?(.+)', event_text)
        if match:
            return match.group(1).strip()
        else:
            return event_text.strip()
        

    def start_date(self, format='csv'):
        return self.format_date(self.row[DATE], format)
    
    def end_date(self, format='csv'):
        return self.format_date(self.row[DATE], format)
    

    def format_date(self, date, format='csv'):
        if format == 'csv':
            return date.strftime('%m/%d/%Y')
        elif format == 'ical':
            return date.strftime('%Y%m%dT%H%M%S')
        return date
    
    def start_time(self, format='csv'):
        return self.format_time(self.row[START_TIME], format)
    
    def end_time(self, format='csv'):
        return self.format_time(self.row[END_TIME], format)

    def format_time(self, time, format='csv'):
        if not time:
            return ''
        if isinstance(time, str):
            time = datetime.strptime(time, '%H:%M').time().strftime('%I:%M %p')
        if format == 'csv':
            return time.strftime('%I:%M %p')
        elif format == 'ical':
            return time.strftime('%H%M%S')
        return time


    def to_csv_dict(self):
        return {
            'Subject': self.name,
            'Start Date': self.start_date,
            'Start Time': self.start_time,
            'End Date': self.end_date,
            'End Time': self.end_time,
            'All Day Event': self.all_day_event,
            'Description': self.description,
            'Location': self.location,
            'Private': False
        }

input_file = conf.input_csv

df = pd.read_excel(input_file)
# convert nan to empty string
df = df.fillna('')

new_csv_rows = []   
for i, row in df.iterrows():
    event = EventRow(row)
    new_csv_rows.append(event.to_csv_dict())

csv_file = conf.output_csv
with open(csv_file, 'w', newline='') as file:
    writer = csv.DictWriter(file, fieldnames=new_csv_rows[0].keys())
    writer.writeheader()
    for row in new_csv_rows:
        writer.writerow(row)

