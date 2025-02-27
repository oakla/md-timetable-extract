import etl
input_file = r"content\input_pdfs\2025 Timetable _Student_Version.V1.a.pdf"
week_1 = etl.get_weekly_calendar_views(input_file, pages='1')[0].df