"""
Script to randomly sample up to 20 rows from each CSV file in flask_apis/CSVs
and save them to a new folder flask_apis/CSVs_sampled
"""
import pandas as pd
import os
from pathlib import Path

def sample_csv_files(input_dir, output_dir, max_rows=20):
    """
    Randomly sample up to max_rows from each CSV file in input_dir
    and save to output_dir

    Args:
        input_dir: Directory containing CSV files to sample
        output_dir: Directory to save sampled CSV files
        max_rows: Maximum number of rows to sample (default: 20)
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Get all CSV files in input directory
    csv_files = [f for f in os.listdir(input_dir) if f.endswith('.csv')]

    print(f"Found {len(csv_files)} CSV files to process")

    for csv_file in csv_files:
        input_path = os.path.join(input_dir, csv_file)
        output_path = os.path.join(output_dir, csv_file)

        try:
            # Read the CSV file
            df = pd.read_csv(input_path)

            # Calculate number of rows to sample
            n_rows = min(len(df), max_rows)

            # Randomly sample rows
            if len(df) > max_rows:
                sampled_df = df.sample(n=n_rows, random_state=42)
            else:
                sampled_df = df

            # Sort by index to maintain some order
            sampled_df = sampled_df.sort_index()

            # Save to output directory
            sampled_df.to_csv(output_path, index=False)

            print(f"[OK] {csv_file}: Sampled {n_rows} rows from {len(df)} total rows")

        except Exception as e:
            print(f"[ERROR] Error processing {csv_file}: {str(e)}")

    print(f"\nSampled CSV files saved to: {output_dir}")

if __name__ == "__main__":
    # Define input and output directories (relative to script location)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(script_dir, "CSVs")
    output_dir = os.path.join(script_dir, "CSVs_sampled")

    # Sample up to 20 rows from each CSV
    sample_csv_files(input_dir, output_dir, max_rows=20)
