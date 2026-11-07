from preprocessing.cleaning import clean_data
from preprocessing.metadata import extract_metadata
import pandas as pd
from pathlib import Path
import os


# Folder for cleaned datasets
CLEANED_FOLDER = "cleaned_data"
Path(CLEANED_FOLDER).mkdir(exist_ok=True)


def preprocess_dataset(filepath):
    """
    Read dataset
    Clean dataset
    Save cleaned dataset
    Extract metadata
    """

    # Read dataset
    if filepath.endswith(".csv"):
        df = pd.read_csv(filepath)
    else:
        df = pd.read_excel(filepath)

    # Clean dataset
    cleaned_df = clean_data(df)

    # Create cleaned filename
    filename = os.path.basename(filepath)
    name, ext = os.path.splitext(filename)

    cleaned_path = os.path.join(
        CLEANED_FOLDER,
        f"{name}_cleaned.csv"
    )

    # Save cleaned dataset
    cleaned_df.to_csv(cleaned_path, index=False)

    # Extract metadata
    metadata = extract_metadata(cleaned_df)

    return cleaned_df, cleaned_path, metadata