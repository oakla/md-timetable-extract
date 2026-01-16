from dataclasses import dataclass
import pandas as pd
import re


def get_week_number(calendar_df: pd.DataFrame) -> str:
    """
    Returns the week number from the calendar dataframe.

    Current version assumptions:
        - The first cell of the table contains the week name, e.g. "Week 01"
        - The week number is preceded by the word "Week"
        - If the first cell contains "Key", then this is not a calendar table and
        `None` is returned. (NOTE: This should be handled before calling this function)
    
    Args:
        - calendar_df (pd.DataFrame): The dataframe representing a 1-page, 1-week 
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



@dataclass
class CalendarWeekView:
    week: int
    df: pd.DataFrame
    

@dataclass
class ScrapedWeekRaw:
    page_number: int
    df: pd.DataFrame
    date_row_index: int = None
    time_column_index: int = None
    is_valid: bool = None


    def __post_init__(self):
        self.is_valid = self.is_calendar_view_df_valid()


    @classmethod
    def from_df(cls, page_number: int, df: pd.DataFrame):
        return ScrapedWeekRaw(page_number, df)
    

    def is_calendar_view_df_valid(self) -> bool:
        
        # assume second row is time header + dates header
        # example:
        # Time | Monday <date> | Tuesday <date> | ...
        EXPECTED_NUM_COLUMNS = 6 # Time + 5 weekdays
        self.date_row_index = self.find_header_row_index()
        if self.date_row_index == -1:
            print(f"    - No valid header row found in extracted calendar view")
            return False
        header_row = self.df.iloc[self.date_row_index]
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
        

        # TODO: this call maybe redundant since this check is in `structs.find_header_row_index`
        if not are_date_headers_valid(header_row):
            print(f"    - Invalid date headers found in extracted calendar view")
            return False
        
        self.is_valid = True
        return True
    

    def find_header_row_index(self) -> int:
        """Header row expectation:
        Time | [day] <date> | [day] <date> | ...
        Returns the index of the header row, or -1 if not found.
        """

        for i, row in self.df.iterrows():
            first_cell = row.iloc[0].strip().lower()
            if first_cell == 'time':
                self.time_column_index = 0
                self.date_row_index = i
                if are_date_headers_valid(row):
                    return i
        return -1
    

