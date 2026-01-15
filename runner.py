import pandas as pd 
import octk

from md_timetable_extract import extract, structs, process_timetable, post_processing
import conf

START_FROM_PAGE = 1
IGNORE_PAGES = [14, 19, 20]


input_file = conf.input_timetable
calendar_views: list[structs.CalendarWeekView] = extract.get_weekly_calendar_views(input_file, ignore_pages=IGNORE_PAGES, start_page=START_FROM_PAGE)

all_events = []
for calendar_view in calendar_views:
    week_i_events:list[dict] = process_timetable.process_week_days(calendar_view.week, calendar_view.df)
    all_events.extend(week_i_events)

df = pd.DataFrame(all_events)
df = post_processing.post_process_events(df)

output_file = octk.uniquify(conf.scraped_output_path)

extra_columns = [
    "Label",
    "watched",
    "Partial",
    "Notes-Done", 
    "Skip",
    "Note",
    "System",
    "Milestone",
]

# add extra columns with empty values
for col in extra_columns:
    df[col] = ""


# if column called 'week' exists, rename it to 'wk'
if 'week' in df.columns:
    df = df.rename(columns={'week': 'wk'})


# reorder columns
df = df[[
    "Label",
	"watched",
	"Partial",
	"Notes-Done",
	"Skip",
	"session_type",
	"Note",
	"wk",
	"subject",
	"presenter",
	"System",
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
