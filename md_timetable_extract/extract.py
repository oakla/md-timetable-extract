# Description: Scrape the timetable into a dataframes that represent
# week-long calendar layouts. i.e. Days as columns, & time slots as rows.

from copy import Error
import camelot
import pandas as pd
from md_timetable_extract import structs
import re


pd.options.mode.chained_assignment = None

def is_key_table(table: camelot.core.Table) -> bool:
    return table.df.iloc[0, 0].strip().lower() == 'key'

def is_valid_time_value(time_str: str) -> bool:
    """Check if a string is a valid time value in HH:MM format.
    Valid examples: '09:00', '14:30', '8', '08', '12', '23:59', '8.00', '08.00'
    """
    isValid = True
    pattern = r'^\d{1,2}([:\.]\d{2})?$'
    if re.match(pattern, time_str):
        if ':' in time_str:
            hours, minutes = map(int, time_str.split(':'))
            if 0 <= hours < 24 and 0 <= minutes < 60:
                return True
        elif '.' in time_str:
            hours, minutes = map(int, time_str.split('.'))
            if 0 <= hours < 24 and 0 <= minutes < 60:
                return True
        else:
            hours = int(time_str)
            if 0 <= hours < 24:
                return True
    return False


def standardize_time_format(time_str: str) -> str:
    """Convert time string to HH:MM format.
    Examples:
        '9' -> '09:00'
        '14:30' -> '14:30'
        '8.00' -> '08:00'
    """
    if '.' in time_str:
        hours, minutes = map(int, time_str.split('.'))
    elif ':' in time_str:
        hours, minutes = map(int, time_str.split(':'))
    else:
        hours = int(time_str)
        minutes = 0

    return f"{hours:02}:{minutes:02}"


def standardize_time_column(df: pd.DataFrame, time_col_name: str = 'Time') -> pd.DataFrame:
    """Standardize the time column in the dataframe to HH:MM format."""
    for i, row in df.iterrows():
        time_str = row[time_col_name].strip()
        if is_valid_time_value(time_str):
            standardized_time = standardize_time_format(time_str)
            df.at[i, time_col_name] = standardized_time
        else:
            raise ValueError(f"Invalid time value found: {time_str}")
    return df


# TODO: delete me
# def get_week_number(calendar_df: camelot.core.Table) -> str:
#     """
#     Returns the week number from the calendar dataframe.

#     Current version assumptions:
#         - The first cell of the table contains the week name, e.g. "Week 01"
#         - The week number is preceded by the word "Week"
#         - If the first cell contains "Key", then this is not a calendar table and
#         `None` is returned. (NOTE: This should be handled before calling this function)
    
#     Args:
#         - calendar_df (camelot.core.Table): The dataframe representing a 1-page, 1-week 
#         calendar view.

#     """
#     table_name = calendar_df.iloc[0, 0]
#     if table_name.strip().lower() == 'key':
#         return None
#     match = re.search(r'Week\s*(\d+)', table_name, re.IGNORECASE)
#     if not match:
#         raise ValueError(f"Could not find week number in table name: {table_name}")
#     week_number = match.group(1)
#     # if less than 10, add a 0
#     if len(week_number) < 2:
#         week_number = '0' + week_number
#     return week_number


# entry point
def get_weekly_calendar_views(pdf_path: str, ignore_pages:list[int], start_page:int = 1, pages='all'
                                ) -> list[structs.CalendarWeekView]:
    """Extracts weekly calendar views from a timetable PDF.
    
    Any pages before `start_page` or in `ignore_pages` are skipped

    """
    # TODO: add GUI to select line_scale

    invalid_extractions = {
        # page number - scale tried: df
    }
    
    handler = camelot.handlers.PDFHandler(pdf_path)
    page_numbers = handler._get_pages(pages)
    page_numbers = [p for p in page_numbers if int(p) >= start_page]
    page_numbers = [p for p in page_numbers if p not in ignore_pages]
    print(f"Processing pages: {page_numbers}")

    weekly_calendar_views = []
    for i, page in enumerate(page_numbers):
        extraction_successful = False
        scales_to_try = [60, 40, 80, 100]
        while not extraction_successful and scales_to_try:
            line_scale = scales_to_try.pop(0)
            print(f"  - Processing page {page} with line_scale={line_scale}")
            calendar_df: pd.DataFrame = extract_calendar_page_view_as_df(pdf_path, page=str(page), line_scale=line_scale)

            scraped_week_raw = structs.ScrapedWeekRaw.from_df(page, calendar_df)
            if scraped_week_raw.is_valid:
                print(f"    - Found valid calendar table on page {page} with line_scale={line_scale}")
                extraction_successful = True
            else:
                invalid_extractions[f"p{page}-scale {line_scale}"] = scraped_week_raw.df
                print(f"    ! No valid calendar tables found on page {page} with line_scale={line_scale}")
                line_scale += 20
        
        if not extraction_successful:
            print(f"  ! Failed to extract valid calendar table on page {page} after trying multiple line scales")
            continue

        week_number = structs.get_week_number(scraped_week_raw.df)
        try:
            interpolated_df = standardise_week_view(scraped_week_raw)
        except Exception as e:
            print(f"Error processing week {week_number}: {e}")
            continue
        weekly_calendar_views.append(structs.CalendarWeekView(int(week_number), interpolated_df))

    return weekly_calendar_views


def extract_calendar_page_view_as_df(pdf_path: str, page:str, line_scale) -> pd.DataFrame:
    """Extracts a single page calendar view from a PDF and returns it as a DataFrame
    *without* rearranging cells.
    Assumes exactly one calendar table per page, and ignores any 'Key' tables."""
    tables = camelot.read_pdf(
        pdf_path, flavor='lattice', 
        line_scale=line_scale, 
        copy_text=['v', 'h'], 
        pages=page
        )
    if len(tables) == 0:
        raise ValueError(f"No tables found on page {page}")
    
    calendar_index = 0
    if len(tables) > 1:
        for i, table in enumerate(tables):
            if is_key_table(table):
                print(f"  - Ignoring 'Key' table on page {page}")
            else:
                calendar_index = i
                break
    calendar_df = tables[calendar_index].df
    return calendar_df


def update_minute_time_slot(time_str: str, new_minute: int) -> str:
    """Update the minute part of a time string in HH:MM format."""
    hours, _ = time_str.split(":")
    return f"{hours}:{new_minute:02}"


def standardise_week_view(scraped_week_table: structs.ScrapedWeekRaw) -> pd.DataFrame:
    """Interpolate a week view dataframe to ensure all time slots are present"""
    base_df = scraped_week_table.df.copy()


    # Create a new dataframe with standardized column names and time slots
    # Copy column names 
    columns = base_df.iloc[scraped_week_table.date_row_index]
    # Make first column should 'Time'
    columns.iloc[0] = 'Time'
    # rename duplicate columns
    columns = [f'{col} ({i})' if columns.duplicated().iloc[i] else col for i, col in enumerate(columns)]
    
    base_df.columns = columns
    
    # get rows where time contains 'online'
    try:
        online_rows = base_df[base_df['Time'].str.contains('online', case=False)]
    except Exception as e:
        raise Exception(f"Error occurred while extracting online rows: {e}")

    # find first row with number in the time column
    is_start_found = False
    for i, row in base_df.iterrows():
        if is_valid_time_value(row.iloc[0]):
            is_start_found = True
            break
    if not is_start_found:
        raise ValueError("Could not find start of time slots in timetable.")
    time_start_row = i

    # make new table starting from time_start_row (i.e. drop earlier rows, then add online rows later)
    class_time_week_view_df = base_df.iloc[time_start_row:]
    class_time_week_view_df.reset_index(drop=True, inplace=True)

    class_time_week_view_df = standardize_time_column(class_time_week_view_df, time_col_name='Time')

    # Find and save the indices of all rows which represent the start of a half-hour slot
    half_past_rows = []
    max_index = len(class_time_week_view_df) - 1
    for i, row in class_time_week_view_df.iterrows():
        start_time = class_time_week_view_df.loc[i, 'Time'].strip()
        if start_time.isdigit() and len(start_time) < 2:
            class_time_week_view_df.loc[i, 'Time'] = '0' + start_time
        if i+1 == max_index:
            break
        if  start_time == class_time_week_view_df.loc[i+1, 'Time']:
            # there is a duplicated time 
            # we assume this to be the start of a half-hour slot 
            half_past_rows.append(i+1)

    # Scan the timetable. 
    # If the timeslot is in the half_past_rows list, add ':30' to the time
    # Else, add ':00' to the time
    # Also, create half-hour slots that don't already exist
    new_half_past_rows = []
    for i, row in class_time_week_view_df.iterrows():
        if i in half_past_rows:
            class_time_week_view_df.loc[i, 'Time'] = update_minute_time_slot(class_time_week_view_df.loc[i, 'Time'], 30)
        elif i+1 in half_past_rows:
            class_time_week_view_df.loc[i, 'Time'] = update_minute_time_slot(class_time_week_view_df.loc[i, 'Time'], 0)
        else:
            new_half_past_rows.append(class_time_week_view_df.iloc[i].to_dict())
            class_time_week_view_df.loc[i, 'Time'] = update_minute_time_slot(class_time_week_view_df.loc[i, 'Time'], 0)

    for d in new_half_past_rows:
        d['Time'] = update_minute_time_slot(d['Time'], 30)

    new_rows_df = pd.DataFrame(new_half_past_rows)

    # Combine existing rows with new half-hour slots
    in_person_rows = pd.concat([class_time_week_view_df, new_rows_df], ignore_index=True)
    # sort by time
    in_person_rows = in_person_rows.sort_values(by='Time')
    full_df = pd.concat([in_person_rows, online_rows], ignore_index=True)
    
    return full_df
