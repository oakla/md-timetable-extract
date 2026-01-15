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

def get_week_number(calendar_df: camelot.core.Table) -> str:
    """
    Returns the week number from the calendar dataframe.

    Current version assumptions:
        - The first cell of the table contains the week name, e.g. "Week 01"
        - The week number is preceded by the word "Week"
        - If the first cell contains "Key", then this is not a calendar table and
        `None` is returned. (NOTE: This should be handled before calling this function)
    
    Args:
        - calendar_df (camelot.core.Table): The dataframe representing a 1-page, 1-week 
        calendar view.

    """
    table_name = calendar_df.iloc[0, 0]
    if table_name.strip().lower() == 'key':
        return None
    match = re.search(r'Week\s*(\d+)', table_name, re.IGNORECASE)
    if not match:
        raise ValueError(f"Could not find week number in table name: {table_name}")
    week_number = match.group(1)
    # if less than 10, add a 0
    if len(week_number) < 2:
        week_number = '0' + week_number
    return week_number


# entry point
def get_weekly_calendar_views(pdf_path: str, ignore_pages:list[int], start_page:int = 1, pages='all') -> list[structs.CalendarWeekView]:
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
            calendar_df = extract_calendar_page_view_as_df(pdf_path, page=str(page), line_scale=line_scale)

            if is_calendar_view_df_valid(calendar_df):
                print(f"    - Found valid calendar table on page {page} with line_scale={line_scale}")
                extraction_successful = True
            else:
                invalid_extractions[f"p{page}-scale {line_scale}"] = calendar_df
                print(f"    ! No valid calendar tables found on page {page} with line_scale={line_scale}")
                line_scale += 20
        
        if not extraction_successful:
            print(f"  ! Failed to extract valid calendar table on page {page} after trying multiple line scales")
            continue

        week_number = get_week_number(calendar_df)
        try:
            interpolated_df = interpolate_week_view(calendar_df)
        except Exception as e:
            print(f"Error processing week {week_number}: {e}")
            continue
        weekly_calendar_views.append(structs.CalendarWeekView(week=week_number, df=interpolated_df))

    return weekly_calendar_views

def are_date_headers_valid(headers: pd.Series) -> bool:
    # check if other columns are valid date headers
    for col in headers[1:]:
        # remove any trailing (\d*) from the column name
        col = col.strip().replace(",", "").replace("/", " ").replace("-", " ")
        # check if col matches format 'Day, DD/MM/YYYY'
        try: 
            _ = pd.to_datetime(col, format='%A %d %B %Y', errors='raise') 
        except Exception as e:
            return False

    return True


def find_header_row_index(df: pd.DataFrame) -> int:
    """Header row expectation:
    Time | [day] <date> | [day] <date> | ...
    Returns the index of the header row, or -1 if not found.
    """

    for i, row in df.iterrows():
        first_cell = row.iloc[0].strip().lower()
        if first_cell == 'time':
            if are_date_headers_valid(row):
                return i
    return -1

def is_calendar_view_df_valid(df: pd.DataFrame) -> bool:
    
    # assume second row is time header + dates header
    # example:
    # Time | Monday <date> | Tuesday <date> | ...
    EXPECTED_NUM_COLUMNS = 6 # Time + 5 weekdays
    header_index = find_header_row_index(df)
    if header_index == -1:
        print(f"    - No valid header row found in extracted calendar view")
        return False
    header_row = df.iloc[header_index]

    # extract may have *more* than expected columns due to the camelot splits columns when there are two events in one time slot
    if len(header_row) < EXPECTED_NUM_COLUMNS:
        print(f"    - Invalid number of columns in calendar view: {len(header_row)}")
        return False
    
    # check that there are an expected number of unique columns
    # e.g. Time + 5 weekdays = 6 unique columns
    if len(header_row.unique()) < EXPECTED_NUM_COLUMNS:
        print(f"    - Not enough unique columns in calendar view: {len(header_row.unique())}")
        return False

    # # todo: only check first column
    # required_columns = ['Time']
    
    # if second_row[0].strip() not in required_columns:
    #     return False
    

    # TODO: this call maybe redundant since we already check this in find_header_row_index
    if not are_date_headers_valid(header_row):
        print(f"    - Invalid date headers found in extracted calendar view")
        return False
    
    return True

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

def is_valid_time_value(time_str: str) -> bool:
    """Check if a string is a valid time value in HH:MM format.
    Valid examples: '09:00', '14:30', '8', '08', '12', '23:59', '8.00', '08.00'
    """
    pattern = r'^\d{1,2}([:\.]\d{2})?$'
    if re.match(pattern, time_str):
        if ':' in time_str:
            hours, minutes = map(int, time_str.split(':'))
            if 0 <= hours < 24 and 0 <= minutes < 60:
                return True
        else:
            hours = int(time_str)
            if 0 <= hours < 24:
                return True
    return False

def interpolate_week_view(df: pd.DataFrame) -> pd.DataFrame:

    base_df = df.copy()

    # Get column names
    columns = base_df.iloc[1]
    # assume that first column should be 'Time'
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
