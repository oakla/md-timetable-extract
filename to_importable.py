# from ics import Calendar, Event
from datetime import datetime
import csv
import re
import pandas as pd
from pathlib import Path

from typing import Literal
# Predefined set of strings type
TimetableField = Literal[
    'week', 'day', 'date', 'event', 'start_time', 'end_time', 
    'location', 'session_type', 'subject', 'presenter', 'groups', 'topic'

]

import md_timetable_extract.conf as conf

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
GROUPS = 'groups'
TOPIC = 'topic'

SUBJECT_ABBREVIATIONS = {
    'Aboriginal Health': 'AH',
    'Anatomy': 'Anat',
    "Behavioural Science": 'Behav Sci',
    "Biochemistry": 'Biochem',
    "Chemical Pathology": 'Chem Path',
    "Clinical": 'Clin',
    "Genetics": 'Gen',
    "Immunology": 'Immun',
    "Microbiology": 'Micro',
    "MicroModule": 'MicroMod',
    "Pathology": 'Path',
    'Pharmacology': 'Pharm',
    'Physiology': 'Phys',
    'Population Health': 'Pop Hlth',
    'Professionalism': 'Prof',
    'Research': 'Res',
}

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

    def __init__(self, row:pd.Series, include_session_type:bool = True):

        self.include_session_type = include_session_type

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

        acc = []
        if self.include_session_type:
            if row[SESSION_TYPE]:
                acc.append(row[SESSION_TYPE])
            if row[SUBJECT]:
                acc.append(SUBJECT_ABBREVIATIONS[row[SUBJECT]] if row[SUBJECT] in SUBJECT_ABBREVIATIONS else row[SUBJECT])
            if row[TOPIC]:
                acc.append(row[TOPIC])
        else:
            if row[SUBJECT]:
                acc.append(SUBJECT_ABBREVIATIONS[row[SUBJECT]] if row[SUBJECT] in SUBJECT_ABBREVIATIONS else row[SUBJECT])
            if row[TOPIC]:
                acc.append(row[TOPIC])

        if not acc:
            return row[DESCRIPTION]
        name = '-'.join(acc)

        # if len(name) > 100:
        #     name = name[:97] + '...'

        return name

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
        # match = re.search(r'\w+:\s?(.+)', event_text)
        # if match:
        #     return match.group(1).strip()
        # else:
        #     return event_text.strip()
        return event_text.strip()
        

    def start_date(self, format='csv'):
        return self.format_date(self.row[DATE], format)
    
    def end_date(self, format='csv'):
        return self.format_date(self.row[DATE], format)
    

    def format_date(self, date:str, format='csv'):
        date = pd.to_datetime(date, errors='coerce')
        if format == 'csv':
            return date.strftime('%m/%d/%Y')
        elif format == 'ical':
            return date.strftime('%Y%m%dT%H%M%S')
        return date
    
    def start_time(self, format='csv'):
        return self.format_time(self.row[START_TIME], format)
    
    def end_time(self, format='csv'):
        return self.format_time(self.row[END_TIME], format)

    def format_time(self, time:str, format='csv'):
        time_value = pd.to_datetime(time, errors='coerce')
        if pd.isna(time_value):
            return ''
        time = time_value.time()
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
    

def df_to_calendar_importable_csv(df: pd.DataFrame, output_file: str, include_session_type: bool = True):
    """
    Converts a DataFrame to a calendar importable CSV format.
    """
    if df.empty:
        raise ValueError("DataFrame is empty. Cannot convert to calendar importable CSV.")
    df = df.fillna('')  # Convert NaN to empty string
    new_csv_rows = []
    
    for i, row in df.iterrows():
        event = EventRow(row, include_session_type=include_session_type)
        new_csv_rows.append(event.to_csv_dict())

    with open(output_file, 'w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=new_csv_rows[0].keys())
        writer.writeheader()
        for row in new_csv_rows:
            writer.writerow(row)


def drop_groups(df: pd.DataFrame, groups: list[str]) -> pd.DataFrame:
    """
    Drops rows from the DataFrame where the 'groups' column contains any of the specified groups.
    """
    if 'groups' not in df.columns:
        raise ValueError("DataFrame does not contain 'groups' column.")
    
    mask = df['groups'].apply(lambda x: not any(group in x for group in groups))
    return df[mask]

input_file = conf.SCRAPED_TIMETABLE_PATH

# if `input_file` does not exist, raise error
if not Path(input_file).exists():
    raise FileNotFoundError(f"Input file {input_file} does not exist.")
# read csv or xlsx file
if input_file.suffix == '.csv':
    df = pd.read_csv(input_file)
elif input_file.suffix in ['.xlsx', '.xls']:
    df = pd.read_excel(input_file)
# convert nan to empty string
df = df.fillna('')

df_non_mandatory = df[df['is_mandatory'] == 0]
assert not df_non_mandatory.empty, "No non-mandatory events found in the input file."
df_mandatory = df[df['is_mandatory'] == 1]

# output_files = {
#     'non_mandatory': conf.importable_calendar_path_for_group('all', mandatory=False]

# if conf.IMPORTABLE_CALENDAR_FILE.exists():
#     input(f"Warning: Overwriting existing file {conf.IMPORTABLE_CALENDAR_FILE}\n Press Enter to continue...")
output_dir = Path(conf.IMPORTABLE_CALENDAR_FILE).parent
output_dir.mkdir(parents=True, exist_ok=True)
df_to_calendar_importable_csv(df_non_mandatory, Path(output_dir, f'{conf.IMPORTABLE_CALENDAR_FILE}(non_mandatory).csv'), include_session_type=False)
df_to_calendar_importable_csv(df_mandatory, Path(output_dir, f'{conf.IMPORTABLE_CALENDAR_FILE}(mandatory).csv'), include_session_type=True)
df_to_calendar_importable_csv(df, Path(output_dir, f'{conf.IMPORTABLE_CALENDAR_FILE}(all).csv'), include_session_type=True)

