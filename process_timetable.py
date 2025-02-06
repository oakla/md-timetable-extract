# Convert the weekly calendar layout into a list of events

import pandas as pd
import re
from datetime import datetime

valid_days = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]

lecture_theatres = ["FJC", "Ross"]

subjects = [
    'Aboriginal Healt'
    'Aboriginal Health'
    "Anatomy",
    "Behavioural Science",
    'Biochemistry',
    "Clinical",
    'Clinical Skills',
    "Pathology",
    "Physiology",
    "Research skills",
    'Pop Health',
    'Popn health',
    'Population Health',
    'Haematology',
    'Health Humanities'
]

type_indicators = {
    "SGL": ["SGL", "Small Group Learning"],
    "Lab": ["Lab group"],
    "Assessment": ["Assessment"],
}


def add_30_minutes(time):
    hour, minute = time.split(":")
    if minute == "00":
        return f"{hour}:30"
    else:
        return f"{int(hour)+1}:00"


def colname_to_date(date, month_format="%B") -> datetime:
    parts = date.replace(",", " ").split()
    if parts[0] not in valid_days:
        print(f"Warning: Unexpected date")
        return None
    # remove text after YYYY
    date = " ".join(parts[:4])

    try:
        return pd.to_datetime(date, format=f"%A %d {month_format} %Y")
    except ValueError:
        return colname_to_date(date, month_format="%b")


def is_online_time_slot(event, time_slot):
    if re.search(r"online", time_slot, flags=re.IGNORECASE):
        return True
    return False


def process_event(event_name:str, week_df, date_col_name, week_number):
    event_name = event_name.strip()

    if event_name == "":
        return None
    start_time = week_df[week_df[date_col_name] == event_name]["Time"].iloc[0]
    end_time = week_df[week_df[date_col_name] == event_name]["Time"].iloc[-1]

    # if date_col_name has (\d*) at the end, remove it
    date_col_name = re.sub(r"\(\d*\)$", "", date_col_name).strip()
    date_obj = colname_to_date(date_col_name)

    session_type = ""
    location = ""
    subject = ""
    if is_online_time_slot(event_name, time_slot=start_time):
        location = "Online"
        session_type = "Lecture"
        start_time = ""
        end_time = ""
    elif re.search(r"\d{2}:\d{2}", start_time):
        if is_online_time_slot(event_name, time_slot=end_time):
            end_time = "19:00"
        else:
            end_time = add_30_minutes(end_time)

    if not session_type:
        for lt in lecture_theatres:
            if lt in event_name:
                location = lt
                session_type = "Lecture"

        for key, values in type_indicators.items():
            for value in values:
                if value in event_name:
                    session_type = key
                    break

    for subject_i in subjects:
        if event_name.startswith(subject_i):
            subject = subject_i
            break

    if not subject:
        candidate_subject = event_name.split(':')[0]
        if len(candidate_subject.split()) < 4:
            subject = candidate_subject

    return {
        "week": week_number,
        "day": date_obj.strftime("%A"),
        "date": date_obj.strftime("%Y-%m-%d"),
        "event": event_name,
        "start_time": start_time,
        "end_time": end_time,
        "location": location,
        "session_type": session_type,
        "subject": subject
    }


def get_days_events(date, week_number, week_df):
    events = week_df[date].unique()
    return [
        x
        for x in [process_event(event, week_df, date, week_number) for event in events]
        if x is not None
    ]


def process_week_days(week_number, week_df):
    events = []
    for date in week_df.columns[1:]:
        day_events = get_days_events(date, week_number, week_df=week_df)
        if day_events is not None:
            events.extend(day_events)

    return events
