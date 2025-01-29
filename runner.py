import camelot
import etl
import process_timetable
import pandas as pd 
import octk

input_file = r"content\input_pdfs\2025 Timetable _Student_Version.V1.a.pdf"
tables = camelot.read_pdf(
    input_file, flavor='lattice', 
    line_scale=40, 
    copy_text=['v', 'h'], 
    pages='all'
    # pages='1-3'
    )

all_weeks = []
for table in tables:
    df = table.df
    # make row 0, column 0 the table name
    table_name = df.iloc[0, 0]
    if table_name.strip().lower() == 'key':
        continue
    # get last numbers in table name
    week_number = table_name.split()[-1]
    # if less than 10, add a 0
    if len(week_number) < 2:
        week_number = '0' + week_number

    timetable_df = etl.table_to_df(df)

    week_i_events:list[dict] = process_timetable.process_week_days(week_number, timetable_df)
    all_weeks.extend(week_i_events)

df = pd.DataFrame(all_weeks)
output_file = octk.uniquify(r"content\output\2025_timetable.csv")

df.to_csv(output_file, index=False)
