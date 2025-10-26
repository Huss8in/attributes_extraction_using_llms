import os
import pandas as pd
import random
import csv

src_folder = 'flask_apis/CSVs'
dest_folder = 'flask_apis/Sampled_CSVs'

os.makedirs(dest_folder, exist_ok=True)

for file in os.listdir(src_folder):
    if file.endswith(".csv"):
        src_path = os.path.join(src_folder, file)
        dst_path = os.path.join(dest_folder, file)

        # Read CSV safely with proper handling of multiline text
        df = pd.read_csv(
            src_path,
            encoding='utf-8',
            quoting=csv.QUOTE_ALL,   # handles text with commas and quotes properly
            quotechar='"',
            skip_blank_lines=True,
            engine='python',         # better for multiline text
            on_bad_lines='skip'      # skip broken lines if any
        )

        # Sample logic
        sample_size = min(500, int(len(df) * 0.1)) if len(df) > 10 else len(df)
        df_sample = df.sample(n=sample_size, random_state=random.randint(1, 9999))

        # Save CSV with quotes preserved
        df_sample.to_csv(dst_path, index=False, quoting=csv.QUOTE_ALL, encoding='utf-8')

        print(f"✅ Sample created: {dst_path} ({len(df_sample)} rows)")
