# Description: Scrape the timetable into a dataframes that represent
# week-long calendar layouts. i.e. Days as columns, & time slots as rows.

import camelot
import pandas as pd
from md_timetable_extract import structs

def is_key_table(table: camelot.core.Table) -> bool:
    return table.df.iloc[0, 0].strip().lower() == 'key'


def get_week_number(calendar_df: camelot.core.Table) -> str:
    table_name = calendar_df.iloc[0, 0]
    if table_name.strip().lower() == 'key':
        return None
    # get last numbers in table name
    week_number = table_name.split()[-1]
    # if less than 10, add a 0
    if len(week_number) < 2:
        week_number = '0' + week_number
    return week_number


def get_weekly_calendar_views(pdf_path: str, pages='all') -> list[structs.CalendarWeekView]:
    tables = camelot.read_pdf(
        pdf_path, flavor='lattice', 
        line_scale=40, 
        copy_text=['v', 'h'], 
        pages=pages
        )
    
    weekly_calender_views = []
    for calendar_df in [table.df for table in tables if not is_key_table(table)]:
        week_number = get_week_number(calendar_df)
        interpolated_df = interpolate_week_view(calendar_df)
        weekly_calender_views.append(structs.CalendarWeekView(week=week_number, df=interpolated_df))

    return weekly_calender_views


def interpolate_week_view(df: pd.DataFrame) -> pd.DataFrame:

    base_df = df.copy()

    # Get column names
    columns = base_df.iloc[1]
    # rename duplicate columns
    columns = [f'{col} ({i})' if columns.duplicated().iloc[i] else col for i, col in enumerate(columns)]
    
    base_df.columns = columns
    
    # get rows where time contains 'online'
    online_rows = base_df[base_df['Time'].str.contains('online', case=False)]
    # find first row with number in the time column
    for i, row in base_df.iterrows():
        if row[0].isdigit():
            break
    time_start_row = i

    # make new table starting from time_start_row
    df = base_df.iloc[time_start_row:]
    df.reset_index(drop=True, inplace=True)

    # Find and save the indices of all rows which represent the start of a half-hour slot
    half_past_rows = []
    max_index = len(df) - 1
    for i, row in df.iterrows():
        start_time = df.loc[i, 'Time'].strip()
        if start_time.isdigit() and len(start_time) < 2:
            df.loc[i, 'Time'] = '0' + start_time
        if i+1 == max_index:
            break
        if  start_time == df.loc[i+1, 'Time']:
            # there is a duplicated time 
            # we assume this to be the start of a half-hour slot 
            half_past_rows.append(i+1)

    # Scan the timetable. 
    # If the timeslot is in the half_past_rows list, add ':30' to the time
    # Else, add ':00' to the time
    # Also, create half-hour slots that don't already exist
    new_half_past_rows = []
    for i, row in df.iterrows():
        if i in half_past_rows:
            df.loc[i, 'Time'] = df.loc[i, 'Time'] + ':30'
        elif i+1 in half_past_rows:
            df.loc[i, 'Time'] = df.loc[i, 'Time'] + ':00'
        else:
            new_half_past_rows.append(df.iloc[i].to_dict())
            df.loc[i, 'Time'] = df.loc[i, 'Time'] + ':00'

    for d in new_half_past_rows:
        d['Time'] = d['Time'] + ':30'

    new_rows_df = pd.DataFrame(new_half_past_rows)

    # Combine existing rows with new half-hour slots
    in_person_rows = pd.concat([df, new_rows_df], ignore_index=True)
    # sort by time
    in_person_rows = in_person_rows.sort_values(by='Time')
    full_df = pd.concat([in_person_rows, online_rows], ignore_index=True)
    
    return full_df
