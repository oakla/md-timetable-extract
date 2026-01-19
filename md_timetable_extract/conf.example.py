from pathlib import Path
# timetable scraping
# paths
# INPUT_TIMETABLE = r"content\input_pdfs\2025 IMED3112 Timetable STUDENTS v1.pdf"
INPUT_TIMETABLE = r"path/to/Timetables/2026 IMS3 Timetable STUDENT v1.2.pdf"

def parse_timetable_filename(timetable_path:Path) -> dict[str, str]:
    """Parse timetable filename to extract year and cohort information.
    
    Example filename: '2025 IMED3112 Timetable STUDENTS v1.pdf'
    Returns: {'year': '2025', 'cohort': 'IMED3112', 'version': 'v1'}
    """
    stem = timetable_path.stem
    parts = stem.split(' ')
    year = parts[0]
    unit = parts[1]
    version = parts[-1]
    return {'year': year, 'unit': unit, 'version': version, 'debug_parts': parts}

OUTPUT_ROOT = Path(r"path\to\output\MD Cohort Shared Folder\Timetables")

def version_output_dir(timetable_path:Path) -> Path:
    """Get output directory for a given timetable version."""
    parsed = parse_timetable_filename(timetable_path)
    dir_name = Path(parsed['unit'], parsed['version'])
    return OUTPUT_ROOT / Path(dir_name)

# Set output dir here
VERSION_OUTPUT_DIR = version_output_dir(Path(INPUT_TIMETABLE))
timetable_name = Path(INPUT_TIMETABLE).stem
SCRAPED_TIMETABLE_PATH = VERSION_OUTPUT_DIR / f"{timetable_name}.csv"

# conversion to calendar importable
# paths
# input_xlsx = r'content\saved-as-xlsx\2025 IMED3112 Timetable (my groups).xlsx'
# INPUT_XLSX = r'E:\OneDrive - UWA\MD1.2\2025 IMED3112 Timetable (my groups).xlsx'
IMPORTABLE_CALENDAR_FILE = VERSION_OUTPUT_DIR / "importable_calendar.csv"

def importable_calendar_path_for_group(group_name: str, mandatory: bool) -> Path:
    suffix = "mandatory" if mandatory else "non_mandatory"
    return VERSION_OUTPUT_DIR / f"importable_calendar_{group_name}_{suffix}.csv"