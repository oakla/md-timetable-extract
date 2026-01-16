import pandas as pd 
import octk

from md_timetable_extract import extract, structs, process_timetable, post_processing
import md_timetable_extract.conf as conf

START_FROM_PAGE = 1
IGNORE_PAGES = [14, 13, 12]  # pages to ignore during extraction
IS_ADD_CUSTOM_COLUMNS = False


calendar_views: list[structs.CalendarWeekView] = extract.get_weekly_calendar_views(conf.INPUT_TIMETABLE, ignore_pages=IGNORE_PAGES, start_page=START_FROM_PAGE)

all_events = []
for calendar_view in calendar_views:
    week_i_events:list[dict] = process_timetable.process_week_days(calendar_view.week, calendar_view.df)
    all_events.extend(week_i_events)

df = pd.DataFrame(all_events)
df = post_processing.post_process_events(df)

output_file = octk.uniquify(conf.SCRAPED_TIMETABLE_PATH)


def add_my_custom_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Add custom columns from first year. Maynot be needed in future versions."""
    # TODO: do you still need this?
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
    return df

if IS_ADD_CUSTOM_COLUMNS:
    df = add_my_custom_columns(df)

if output_file.parent.exists():
    input(f"Output folder already exists: \n\t{output_file.parent}. \nPress Enter to continue...")
output_file.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(output_file, index=False)
