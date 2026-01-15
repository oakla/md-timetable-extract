import pandas as pd 
import octk

from md_timetable_extract import extract, structs, process_timetable, post_processing
import md_timetable_extract.conf as conf

input_file = conf.INPUT_TIMETABLE
calendar_views: list[structs.CalendarWeekView] = extract.get_weekly_calendar_views(input_file, pages='1-2')


all_events = []
for calendar_view in calendar_views:
    week_i_events:list[dict] = process_timetable.process_week_days(calendar_view.week, calendar_view.df)
    all_events.extend(week_i_events)

df = pd.DataFrame(all_events)
df = post_processing.post_process_events(df)

output_file = octk.uniquify(conf.VERSION_OUTPUT_DIR)
df.to_csv(output_file, index=False)