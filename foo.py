import os, sys, time, shutil
import logging
import pandas as pd

from pathlib import Path
from pypdf import PdfReader
from IPython.display import display

import camelot

# Set up logging
logging.getLogger("camelot").setLevel(logging.ERROR)
logging.basicConfig(
    level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Function to delete a directory and its contents
def delete_directory(path):
    try:
        shutil.rmtree(path)
        print(f"Deleted directory: {path}")
    except FileNotFoundError:
        print(f"Directory not found: {path}")
    except Exception as e:
        print(f"Error deleting directory {path}: {e}")


def process_pdf(pdf_file, output_dir):
    print(f"Processing {pdf_file.name}")
    logging.info(f"Processing {pdf_file.name}")

    # Verify PDF can be opened with PdfReader before processing
    try:
        reader = PdfReader(str(pdf_file))
        if len(reader.pages) == 0:
            raise ValueError(f"No pages found in PDF {pdf_file.name}")
    except Exception as e:
        print(f"Failed to open PDF {pdf_file.name} with PdfReader: {e}")
        logging.error(f"Failed to open PDF {pdf_file.name} with PdfReader: {e}")
        return

    # Read tables from the PDF using camelot
    try:
        tables = camelot.read_pdf(str(pdf_file), backend="pdfium")
    except Exception as e:
        print(f"Failed to read PDF {pdf_file.name}: {e}")
        logging.error(f"Failed to read PDF {pdf_file.name}: {e}")
        return

    if len(tables) == 0:
        print(f"No tables detected in {pdf_file.name}")
        logging.warning(f"No tables detected in {pdf_file.name}")
        return

    # Create a subdirectory for this PDF's output
    pdf_output_dir = output_dir / pdf_file.stem
    pdf_output_dir.mkdir(exist_ok=True)

    # Process individual tables
    for i, table in enumerate(tables):
        try:
            # Convert table to pandas DataFrame
            df = table.df

            # Display the DataFrame
            print(f"\nTable {i+1} from {pdf_file.name}:")
            display(df)

            # Save individual table to CSV
            csv_path = pdf_output_dir / f"{pdf_file.stem}_table_{i+1}.csv"
            df.to_csv(csv_path, index=False)
            print(f"Saved to {csv_path}")

            # Log parsing report for each table
            print(f"\nTable {i+1} Parsing Report:")
            logging.info(f"Table {i+1} Parsing Report:")
            print(table.parsing_report)
            logging.info(table.parsing_report)
        except Exception as e:
            print(f"Failed to process or save table {i+1} from {pdf_file.name}: {e}")
            logging.error(
                f"Failed to process or save table {i+1} from {pdf_file.name}: {e}"
            )


# Define input_dir and output_dir
input_dir = Path("content/input_pdfs")
output_dir = Path("content/output")

print(f"Input directory: {input_dir}")
print(f"Output directory: {output_dir}")

# Ensure output directory exists
output_dir.mkdir(exist_ok=True)

# Process each PDF in the input directory
pdf_files = list(input_dir.glob("*.pdf"))
print(f"Found {len(pdf_files)} PDF files")

if len(pdf_files) == 0:
    print("No PDF files found in the input directory.")
    logging.warning("No PDF files found in the input directory.")
else:
    for pdf_file in pdf_files:
        process_pdf(pdf_file, output_dir)

    print("Processing complete. Check the 'output' folder for results.")
    logging.info("Processing complete. Check the 'output' folder for results.")

print("Script execution finished.")