import pandas as pd 
import octk

from md_timetable_extract import extract, structs, process_timetable, post_processing
import md_timetable_extract.conf as conf

START_FROM_PAGE = 1
IGNORE_PAGES = [14, 13, 12]  # pages to ignore during extraction
IS_ADD_CUSTOM_COLUMNS = False
TARGET_PAGES = '3'  # can be 'all' or a string of page numbers like '1,3,5' or a single page like '3'

# df = extract.extract_calendar_page_view_as_df(conf.INPUT_TIMETABLE, "3", line_scale=60)

calendar_views: list[structs.CalendarWeekView] = (
    extract.get_weekly_calendar_views(
        conf.INPUT_TIMETABLE, 
        ignore_pages=IGNORE_PAGES, 
        start_page=START_FROM_PAGE, 
        pages=TARGET_PAGES
        )
)

all_events = []

