import pandas as pd
import numpy as np
from typing import List
from pathlib import Path

NEW_CSV_FILE = r"E:\alexa\Code\proj\md-timetable-extract\content\output\scraped\2025 IMED3112 Timetable STUDENTS v4.csv"
OLD_CSV_FILE = r"E:\alexa\Code\proj\md-timetable-extract\content\output\scraped\2025 IMED3112 Timetable STUDENTS v3(1)(1).csv"

OUTPUT_DIR = r"E:\alexa\Code\proj\md-timetable-extract\content\output\changes"
CHANGES_PREVIOUS_OUTPUT = Path(OUTPUT_DIR, r"previous_events.csv")
CHANGES_CURRENT_OUTPUT = Path(OUTPUT_DIR, r"updated_events.csv")


def compare_csv_files(old_file: str, new_file: str, 
                    comparison_columns: List[str] = None,
                    output_old: str = "changed_rows_old.csv",
                    output_new: str = "changed_rows_new.csv") -> None:
    """
    Compare two CSV files and output changed rows based on specified columns.

    Args:
        old_file: Path to the original CSV file
        new_file: Path to the updated CSV file
        comparison_columns: List of columns to compare (default: ['description', 'date', 'start_time', 'end_time'])
        output_old: Path for output file containing old versions of changed rows
        output_new: Path for output file containing new versions of changed rows
    """

    if comparison_columns is None:
        comparison_columns = ['description', 'date', 'start_time', 'end_time']
    
    # Read the CSV files
    df_old = pd.read_csv(old_file)
    df_new = pd.read_csv(new_file)
    
    # Fill NaN values with empty strings for comparison
    df_old = df_old.fillna('')
    df_new = df_new.fillna('')
    
    # Create comparison keys by concatenating the specified columns
    df_old['comparison_key'] = df_old[comparison_columns].astype(str).agg('|'.join, axis=1)
    df_new['comparison_key'] = df_new[comparison_columns].astype(str).agg('|'.join, axis=1)
    
    # Find rows that exist in old but not in new (deleted/changed)
    old_keys = set(df_old['comparison_key'])
    new_keys = set(df_new['comparison_key'])
    
    # Keys that changed (exist in old but not in new)
    changed_old_keys = old_keys - new_keys
    # Keys that are new (exist in new but not in old)
    changed_new_keys = new_keys - old_keys
    
    # Get the actual changed rows
    changed_old_rows = df_old[df_old['comparison_key'].isin(changed_old_keys)].copy()
    changed_new_rows = df_new[df_new['comparison_key'].isin(changed_new_keys)].copy()
    
    # Remove the comparison_key column before output
    changed_old_rows = changed_old_rows.drop('comparison_key', axis=1)
    changed_new_rows = changed_new_rows.drop('comparison_key', axis=1)
    
    # Output the results
    # create output directory if it doesn't exist
    Path(output_old).parent.mkdir(parents=True, exist_ok=True)
    changed_old_rows.to_csv(output_old, index=False)
    changed_new_rows.to_csv(output_new, index=False)
    
    print(f"Found {len(changed_old_rows)} changed rows (old versions)")
    print(f"Found {len(changed_new_rows)} changed rows (new versions)")
    print(f"Old versions saved to: {output_old}")
    print(f"New versions saved to: {output_new}")

# Example usage
if __name__ == "__main__":
    # Compare two CSV files
    compare_csv_files(
        old_file=OLD_CSV_FILE,
        new_file=NEW_CSV_FILE,
        comparison_columns=['description', 'date', 'start_time', 'end_time'],
        output_old=CHANGES_PREVIOUS_OUTPUT,
        output_new=CHANGES_CURRENT_OUTPUT
    )