from pathlib import Path
# timetable scraping
# paths
# INPUT_TIMETABLE = r"content\input_pdfs\2025 IMED3112 Timetable STUDENTS v1.pdf"
INPUT_TIMETABLE = r"path/to/Timetables/2026 IMS3 Timetable STUDENT v1.2.pdf"

IGNORE_PAGES = [14,19,20]

def parse_timetable_filename(timetable_path:Path) -> dict[str, str]:
    """Parse timetable filename to extract year and cohort information.
    
    Examples: 
        filename: '2025 IMED3112 Timetable STUDENTS v1.pdf'
        Returns: {'year': '2025', 'cohort': 'IMED3112', 'version': 'v1'}
        filename: '2026-IMED3111-Timetable.DRAFT.-V5.pdf'
        Returns: {'year': '2026', 'cohort': 'IMED3111', 'version': 'V5'}
        filename: 'IMS2 2026 DRAFT - Student version 1.pdf'
        Returns: {'year': '2026', 'cohort': 'IMS2', 'version': '1'}
    """
    stem = timetable_path.stem
    stem = stem.replace("-", " ")
    return_dict = {
        'year': None,
        'unit': None,
        'version': None,
        'original_timetable_name': stem, 
    }
    parts = stem.split(' ')
    if year := next((part for part in parts if part.isdigit() and len(part) == 4), None):
        return_dict['year'] = year
        parts.remove(year)
    if not parts:
        return return_dict
    unit = parts[0]
    return_dict['unit'] = unit
    parts.remove(unit) 
    if not parts:
        return return_dict
    version = ' '.join(parts)
    return_dict['version'] = version
    return return_dict

OUTPUT_ROOT = Path(r"E:\OneDrive - UWA\00-My-Stuff\UWA MD\MD Cohort Shared Folder\Timetables")

def version_output_dir(timetable_path:Path) -> Path:
    """Get output directory for a given timetable version."""
    parsed = parse_timetable_filename(timetable_path)
    if not parsed['unit'] or not parsed['version']:
        dir_name = parsed['original_timetable_name']
    else:
        dir_name = Path(parsed['unit'], parsed['version'])
    return OUTPUT_ROOT / Path(dir_name)

# Set output dir here
VERSION_OUTPUT_DIR = version_output_dir(Path(INPUT_TIMETABLE))
timetable_name = Path(INPUT_TIMETABLE).stem
SCRAPED_TIMETABLE_OUTPUT_PATH = VERSION_OUTPUT_DIR / f"{timetable_name}.csv"

# conversion to calendar importable
# paths
# input_xlsx = r'content\saved-as-xlsx\2025 IMED3112 Timetable (my groups).xlsx'
# INPUT_XLSX = r'E:\OneDrive - UWA\MD1.2\2025 IMED3112 Timetable (my groups).xlsx'
IMPORTABLE_CALENDAR_FILE = VERSION_OUTPUT_DIR / "importable_calendar.csv"

def importable_calendar_path_for_group(group_name: str, mandatory: bool) -> Path:
    suffix = "mandatory" if mandatory else "non_mandatory"
    return VERSION_OUTPUT_DIR / f"importable_calendar_{group_name}_{suffix}.csv"