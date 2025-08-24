import pandas as pd 
import octk

from md_timetable_extract import extract, structs, process_timetable, post_processing
import conf

input_file = conf.input_timetable
calendar_views: list[structs.CalendarWeekView] = extract.get_weekly_calendar_views(input_file)

all_events = []
for calendar_view in calendar_views:
    week_i_events:list[dict] = process_timetable.process_week_days(calendar_view.week, calendar_view.df)
    all_events.extend(week_i_events)

df = pd.DataFrame(all_events)
df = post_processing.post_process_events(df)

output_file = octk.uniquify(conf.scraped_output_path)

"week",
"day",
"date",
"description",
"start_time",
"end_time",
"location",
"session_type",
"subject",
"presenter",
"groups",
"topic",
"is_mandatory",
"event_length",

extra_columns = [
    "Label",
    "watched",
    "Partial",
    "Review from",
    "Note",
    "Skip",
    "Milestone",
]

# add extra columns with empty values
for col in extra_columns:
    df[col] = ""

# reorder columns
df = df[[
    "Label",
    "watched",
    "Partial",
    "session_type",
    "Review from",
    "Note",
    "presenter",
    "Skip",
    "week",
    "subject",
    "event_length",
    "description",
    "topic",
    "day",
    "date",
    "start_time",
    "end_time",
    "location",
    "groups",
    "Milestone",
    "is_mandatory",
]]


df.to_csv(output_file, index=False)
