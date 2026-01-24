# Convert the weekly calendar layout into a list of events

import pandas as pd
import re
from datetime import datetime
from dateutil.parser import parse as dateutil_parse

valid_days = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]

def add_30_minutes(time):
    hour, minute = time.split(":")
    if minute == "00":
        return f"{hour}:30"
    else:
        return f"{int(hour)+1}:00"


def is_online_time_slot(event, time_slot):
    if re.search(r"online", time_slot, flags=re.IGNORECASE):
        return True
    return False


def process_event(event_description:str, week_df:pd.DataFrame, date_col_name:str, week_number:int) -> dict | None:
    event_identifier = event_description
    event_description = re.sub(r'\s+',' ', event_description).strip()

    if event_description == "":
        return None
    start_time = week_df[week_df[date_col_name] == event_identifier]["Time"].iloc[0]
    end_time = week_df[week_df[date_col_name] == event_identifier]["Time"].iloc[-1]


    # Handle duplicate date columns (i.e. if date_col_name has (\d*) at the end, remove it)
    date_col_name = re.sub(r"\(\d*\)$", "", date_col_name).strip()
    date_obj = dateutil_parse(date_col_name, fuzzy=True)

    session_type = ""
    location = ""
    subject = ""
    if is_online_time_slot(event_description, time_slot=start_time):
        location = "Online"
        session_type = "Lecture"
        start_time = ""
        end_time = ""
    elif re.search(r"\d{2}:\d{2}", start_time):
        if is_online_time_slot(event_description, time_slot=end_time):
            end_time = "19:00"
        else:
            end_time = add_30_minutes(end_time)

    return {
        "week": week_number,
        "day": date_obj.strftime("%A"),
        "date": date_obj.strftime("%Y-%m-%d"),
        "description": re.sub(r'\s+', ' ', event_identifier.replace("\n", " ")),
        "start_time": start_time,
        "end_time": end_time,
        "location": location,
        "session_type": session_type,
        "subject": subject
    }


def get_days_events(date:str, week_number:int, week_df:pd.DataFrame) -> list[dict]:
    events = week_df[date].unique()
    return [
        x
        for x in [process_event(event, week_df, date, week_number) for event in events]
        if x is not None
    ]


def process_week_days(week_number:int, weekview_df:pd.DataFrame) -> list[dict]:
    """Transform a 'week view' dataframe (i.e. with days/dates as columns) into a list of events.
    Each event is represented as a dictionary with keys like 'week', 'day', 'date', 'description', 'etc'.

    The returned list is suitable for conversion into a pandas DataFrame for further processing.
    
    """
    events = []
    for date in weekview_df.columns[1:]:
        day_events = get_days_events(date, week_number, week_df=weekview_df)
        if day_events is not None:
            events.extend(day_events)

    return events
