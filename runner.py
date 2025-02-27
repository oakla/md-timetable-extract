import pandas as pd 
import octk

from md_timetable_extract import structs, process_timetable, etl, post_processing
import conf

input_file = r"content\input_pdfs\2025 Timetable _V2.pdf"
calendar_views: list[structs.CalendarWeekView] = etl.get_weekly_calendar_views(input_file)

all_events = []
for calendar_view in calendar_views:
    week_i_events:list[dict] = process_timetable.process_week_days(calendar_view.week, calendar_view.df)
    all_events.extend(week_i_events)

df = pd.DataFrame(all_events)
df = post_processing.post_process_events(df)

output_file = octk.uniquify(r"content\output\scraped\2025_timetable.csv")
df.to_csv(output_file, index=False)
