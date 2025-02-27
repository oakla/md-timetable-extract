# MD Timetable Extractor
Extract timetable information from a PDF provided by UWA for the MD course.

## Installation

Assumes you have python installed. The script was developed using python 3.13.1.

Create a virtual environment (optional but recommended)
```bash
python -m venv .venv
```

Activate the virtual environment

Windows
```bash
.venv\Scripts\activate
```

Linux/Mac
```bash
source .venv/bin/activate
```

Install the required packages
```bash
pip install -r requirements.txt
```

## Usage

edit `conf.py` to set input and output paths. You can call them whatever you want.
```py
# conf.py

# timetable scraping
# paths
input_timetable = r"path/to/original/pdf/file.pdf"
scraped_output_path = r"path/to/save/output.csv"

# conversion to calendar importable
# paths
input_csv = r"path/to/a/saved/output.csv"
output_csv = r"path/to/save/calendar_importable.csv"
```

Run the scripts
```bash
# scrape the timetable
python runner.py

# convert the scraped timetable to a calendar importable format
python to_importable.py
```
