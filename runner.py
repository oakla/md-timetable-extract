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

    
output_file.parent.mkdir(parents=True, exist_ok=True)
try:
    df.to_csv(output_file, index=False)
except Exception as e:
    print(f"Error saving CSV file: {e}")
else:
    print(f"Scraped timetable saved to: {output_file}")


# TODO: address or suppress error message after running the script:
"""
Exception ignored in atexit callback <function rmtree at 0x0000029B82D918A0>:
Traceback (most recent call last):
  File "%PYENV_DIR%\pyenv-win\versions\3.13.1\Lib\shutil.py", line 790, in rmtree
    return _rmtree_unsafe(path, onexc)
  File "%PYENV_DIR%\pyenv-win\versions\3.13.1\Lib\shutil.py", line 629, in _rmtree_unsafe
    onexc(os.unlink, fullname, err)
  File "%PYENV_DIR%\pyenv-win\versions\3.13.1\Lib\shutil.py", line 625, in _rmtree_unsafe
    os.unlink(fullname)
PermissionError: [WinError 32] The process cannot access the file because it is being used by another process: '%LOCALAPPDATA%\\Temp\\tmp6bj6p8yj\\page-11.pdf'
Exception ignored in atexit callback <function rmtree at 0x0000029B82D918A0>:
Traceback (most recent call last):
  File "%PYENV_DIR%\pyenv-win\versions\3.13.1\Lib\shutil.py", line 790, in rmtree
    return _rmtree_unsafe(path, onexc)
  File "%PYENV_DIR%\pyenv-win\versions\3.13.1\Lib\shutil.py", line 629, in _rmtree_unsafe
    onexc(os.unlink, fullname, err)
  File "%PYENV_DIR%\pyenv-win\versions\3.13.1\Lib\shutil.py", line 625, in _rmtree_unsafe
    os.unlink(fullname)
PermissionError: [WinError 32] The process cannot access the file because it is being used by another process: '%LOCALAPPDATA%\\Temp\\tmph0n7uzmg\\page-10.pdf'
"""