import os
import pandas as pd
import random
import csv

src_folder = 'CSVs'
dest_path = 'mega_dataset.csv'

all_samples = []

for file in os.listdir(src_folder):
    if file.endswith(".csv"):
        src_path = os.path.join(src_folder, file)

        # Extract source name (remove 'Cleaned_' and '.csv')
        source_name = os.path.splitext(file)[0].replace("Cleaned_", "").strip()

        # Read CSV safely
        df = pd.read_csv(
            src_path,
            encoding='utf-8',
            quoting=csv.QUOTE_ALL,
            quotechar='"',
            skip_blank_lines=True,
            engine='python',
            on_bad_lines='skip'
        )

        # Take random 80 rows (or all if less)
        sample_size = min(80, len(df))
        df_sample = df.sample(n=sample_size, random_state=random.randint(1, 9999))

        # Add 'source' column at first position
        df_sample.insert(0, 'source', source_name)

        all_samples.append(df_sample)
        print(f"✅ Added {sample_size} rows from {source_name}")

# Combine all samples into one DataFrame
mega_df = pd.concat(all_samples, ignore_index=True)

# Save to single CSV
mega_df.to_csv(dest_path, index=False, quoting=csv.QUOTE_ALL, encoding='utf-8')

print(f"\n🚀 Mega dataset created successfully at: {dest_path}")
print(f"Total rows: {len(mega_df)}")
