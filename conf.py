from pathlib import Path
# timetable scraping
# paths
# input_timetable = r"content\input_pdfs\2025 IMED3112 Timetable STUDENTS v1.pdf"
input_timetable = r"E:\alexa\Code\proj\md-timetable-extract\content\input_pdfs\2025 IMED3112 Timetable STUDENTS v4.pdf"
timetable_name = Path(input_timetable).stem
scraped_output_path = fr"content\output\scraped\{timetable_name}.csv"

# conversion to calendar importable
# paths
# input_xlsx = r'content\saved-as-xlsx\2025 IMED3112 Timetable (my groups).xlsx'
input_xlsx = r'E:\OneDrive - UWA\MD1.2\2025 IMED3112 Timetable (my groups).xlsx'
output_csv = r'content\output\importables\output.csv'
