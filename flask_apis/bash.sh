#!/bin/bash

# Loop through all CSV files in the CSVs folder
for file in CSVs/*.csv; do
  # Define output file path
  output="CSVs/output_$(basename "$file")"
  
  echo "Processing: $file -> $output"
  
  # Send POST request to the API
  curl -X POST http://localhost:5000/process_csv_pipeline \
  -H "Content-Type: application/json" \
  -d "{\"csv_path\": \"$file\", \"output_path\": \"$output\", \"translate_fields\": [\"Item (EN)\", \"Description (EN)\"]}"
  
  echo "Done with $file"
  echo "-----------------------------------------"
done
