import etl
import conf

input_file = conf.input_timetable
week_1 = etl.get_weekly_calendar_views(input_file, pages='1')[0].df