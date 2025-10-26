"""
Batch Processing Script for Master Pipeline API
Processes all CSV files in a specified folder
"""

import requests
import json
import os
import glob
from datetime import datetime

# API Configuration
API_URL = "http://localhost:5000/process_csv_pipeline"
HEALTH_URL = "http://localhost:5000/health"


def test_health():
    """Test if the API is running"""
    try:
        response = requests.get(HEALTH_URL)
        if response.status_code == 200:
            print("✓ API is healthy and running!")
            return True
        else:
            print("✗ API health check failed")
            return False
    except Exception as e:
        print(f"✗ Could not connect to API: {e}")
        print("  Make sure the API is running with: python flask_apis/api_master_pipeline.py")
        return False


def process_single_csv(csv_path, output_folder=None, translate_fields=None):
    """Process a single CSV file through the master pipeline"""

    # Prepare output path
    if output_folder:
        os.makedirs(output_folder, exist_ok=True)
        filename = os.path.basename(csv_path)
        base_name = os.path.splitext(filename)[0]
        output_path = os.path.join(output_folder, f"{base_name}_processed.csv")
    else:
        output_path = csv_path.replace('.csv', '_processed.csv')

    # Prepare request payload
    payload = {
        "csv_path": csv_path,
        "output_path": output_path
    }

    if translate_fields:
        payload["translate_fields"] = translate_fields

    print(f"\n{'='*60}")
    print(f"Processing: {csv_path}")
    print(f"Output: {output_path}")
    print(f"{'='*60}\n")

    try:
        # Make the request
        response = requests.post(API_URL, json=payload, timeout=7200)  # 2 hour timeout

        if response.status_code == 200:
            result = response.json()
            print(f"\n✓ Successfully processed!")
            print(f"  Rows processed: {result.get('processed_rows')}")
            return {
                "success": True,
                "csv_path": csv_path,
                "output_path": output_path,
                "rows": result.get('processed_rows')
            }
        else:
            print(f"\n✗ Error: {response.status_code}")
            error_msg = response.json()
            print(error_msg)
            return {
                "success": False,
                "csv_path": csv_path,
                "error": error_msg
            }

    except requests.exceptions.Timeout:
        error = "Request timed out"
        print(f"✗ {error}")
        return {
            "success": False,
            "csv_path": csv_path,
            "error": error
        }
    except Exception as e:
        error = str(e)
        print(f"✗ Error: {error}")
        return {
            "success": False,
            "csv_path": csv_path,
            "error": error
        }


def batch_process_folder(folder_path, output_folder=None, translate_fields=None, file_pattern="*.csv"):
    """Process all CSV files in a folder"""

    # Find all CSV files
    search_pattern = os.path.join(folder_path, file_pattern)
    csv_files = glob.glob(search_pattern)

    if not csv_files:
        print(f"\n✗ No CSV files found in: {folder_path}")
        return

    print(f"\n{'='*60}")
    print(f"Batch Processing: {len(csv_files)} CSV files")
    print(f"Folder: {folder_path}")
    if output_folder:
        print(f"Output Folder: {output_folder}")
    print(f"{'='*60}\n")

    # Process each file
    results = []
    start_time = datetime.now()

    for idx, csv_file in enumerate(csv_files, 1):
        print(f"\n[{idx}/{len(csv_files)}] Starting: {os.path.basename(csv_file)}")
        result = process_single_csv(csv_file, output_folder, translate_fields)
        results.append(result)

    # Summary
    end_time = datetime.now()
    duration = end_time - start_time

    print(f"\n\n{'='*60}")
    print(f"BATCH PROCESSING SUMMARY")
    print(f"{'='*60}")
    print(f"Total files: {len(csv_files)}")
    print(f"Successful: {sum(1 for r in results if r['success'])}")
    print(f"Failed: {sum(1 for r in results if not r['success'])}")
    print(f"Duration: {duration}")
    print(f"{'='*60}\n")

    # Detailed results
    print("Detailed Results:")
    print("-" * 60)
    for result in results:
        status = "✓ SUCCESS" if result['success'] else "✗ FAILED"
        filename = os.path.basename(result['csv_path'])
        if result['success']:
            print(f"{status} | {filename} | Rows: {result.get('rows', 0)}")
        else:
            print(f"{status} | {filename} | Error: {result.get('error', 'Unknown')}")

    # Failed files
    failed_files = [r for r in results if not r['success']]
    if failed_files:
        print(f"\n\n{'='*60}")
        print(f"FAILED FILES ({len(failed_files)}):")
        print(f"{'='*60}")
        for failed in failed_files:
            print(f"\nFile: {failed['csv_path']}")
            print(f"Error: {failed.get('error', 'Unknown')}")

    # Save summary to file
    summary_path = os.path.join(output_folder or folder_path, f"processing_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump({
            "total_files": len(csv_files),
            "successful": sum(1 for r in results if r['success']),
            "failed": sum(1 for r in results if not r['success']),
            "duration": str(duration),
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "results": results
        }, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Summary saved to: {summary_path}")


def main():
    """Main function"""
    print("\n" + "="*60)
    print("Master Pipeline - Batch CSV Processor")
    print("="*60)

    # Test health first
    if not test_health():
        print("\nPlease start the API first:")
        print("  python flask_apis/api_master_pipeline.py")
        return

    print("\n" + "="*60)
    print("Configuration")
    print("="*60)

    # Get folder path
    default_folder = "CSVs"
    folder_input = input(f"\nEnter CSV folder path (default: {default_folder}): ").strip()
    folder_path = folder_input if folder_input else default_folder

    if not os.path.exists(folder_path):
        print(f"\n✗ Folder not found: {folder_path}")
        create = input("Create this folder? (y/n): ").strip().lower()
        if create == 'y':
            os.makedirs(folder_path)
            print(f"✓ Created folder: {folder_path}")
            print("Please add CSV files to this folder and run the script again.")
            return
        else:
            return

    # Get output folder
    default_output = os.path.join(folder_path, "processed")
    output_input = input(f"\nEnter output folder path (default: {default_output}): ").strip()
    output_folder = output_input if output_input else default_output

    # Translation option
    translate = input("\nTranslate Item and Description to Arabic? (y/n): ").strip().lower()
    translate_fields = ["Item (EN)", "Description (EN)"] if translate == "y" else []

    # File pattern
    file_pattern = input("\nFile pattern (default: *.csv): ").strip()
    if not file_pattern:
        file_pattern = "*.csv"

    # Confirm
    print(f"\n{'='*60}")
    print("Summary:")
    print(f"  Input Folder: {folder_path}")
    print(f"  Output Folder: {output_folder}")
    print(f"  File Pattern: {file_pattern}")
    print(f"  Translate Fields: {translate_fields if translate_fields else 'None'}")
    print(f"{'='*60}")

    confirm = input("\nProceed with batch processing? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Cancelled.")
        return

    # Start batch processing
    batch_process_folder(folder_path, output_folder, translate_fields, file_pattern)


if __name__ == "__main__":
    main()
