import argparse
import json
import logging
from pathlib import Path
import pandas as pd
import numpy as np

# Clean data in the Louisville Metro KY - Library Collection Inventory
#
# Usage: 
# $ python3 clean.py data/test.csv results/test-clean.csv
#
# where:
#   data/test.csv              = path to the input file
#   results/test-clean.csv     = path to the output file
#
# test input file provided: data/test.csv

def get_file_names() -> tuple:
    """Get the input and output file names from the arguments passed in
    @return a tuple containing (input_file_name, output_file_name)
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", help="Name of the original data file.")
    parser.add_argument("output_file", help="Name of the file for cleaned data.")
    args = parser.parse_args()
    return args.input_file, args.output_file


def validate_columns(df: pd.DataFrame) -> None:
    """Validates that the data in the input file has the expected columns. \
    Exits with an error if the expected columns are not present.
    @param df - The DataFrame object with the data from the input file.
    """
    EXPECTED_COLUMNS = ['BibNum', 'Title', 'Author', 'ISBN', 'PublicationYear', 
        'ItemType','ItemCollection', 'ItemLocation', 'ItemPrice', 'ReportDate']
    if not all(item in list(df.columns) for item in EXPECTED_COLUMNS):
       logging.error('Input file does not have the expected columns.')
       exit(1)
    return None


def build_genre_column(df: pd.DataFrame) -> pd.DataFrame:
    """Creates a new column in the DataFrame called Genre that is based on the\
    ItemCollection column.
    @param df - the original DataFrame
    @return a DataFrame with a new column added
    """
    json_path = Path('data/genre.json')
    with open(json_path, 'r') as json_file:
        genre_data = json.load(json_file)
        genre_conditions = [
            (df['ItemCollection'].isin(genre_data['Fiction'])),
            (df['ItemCollection'].isin(genre_data['Non-Fiction'])),
            (df['ItemCollection'].isin(genre_data['Unknown']))
        ]
        genre_values = ['Fiction', 'Non-Fiction', 'Unknown']
        df['Genre'] = np.select(genre_conditions, genre_values)
        return df


def build_audience_column(df: pd.DataFrame) -> pd.DataFrame:
    """Creates a new column in the DataFrame called Audience that is based on \
        the ItemCollection column.
    @param df - the original DataFrame
    @return a DataFrame with a new column added
    """
    json_path = Path('data/audience.json')
    with open(json_path,'r') as f:
        audience_data = json.load(f)
        audience_conditions = [
            (df['ItemCollection'].isin(audience_data['Adult'])),
            (df['ItemCollection'].isin(audience_data['Teen'])),
            (df['ItemCollection'].isin(audience_data['Children'])),
            (df['ItemCollection'].isin(audience_data['Unknown']))
        ]
        audience_values = ['Adult', 'Teen', 'Children', 'Unknown']
        df['Audience'] = np.select(audience_conditions, audience_values)
        return df


def main() -> None:
    """Main cleaning logic
    """
    logging.info('Getting file names from arguments.')
    input_file, output_file = get_file_names()
    logging.info(f'Input file is: {input_file}')
    logging.info(f'Output file is: {output_file}')
 
    logging.info('Loading data from input file.')
    input_path = Path(input_file)
    if not input_path.exists():
        logging.error(f'Input file not found: {input_file}')
        exit(1)
    books_df = pd.read_csv(input_path)

    logging.info('Validating columns in input file.')
    validate_columns(books_df)

    logging.info('Step 1: Removing unneeded columns.')
    clean_df = books_df.drop(['ISBN','ReportDate'], axis=1)

    logging.info('Step 2: Removing records with empty and invalid PuublicationYear or ItemCollection.')
    clean_df.dropna(subset=['ItemCollection'], inplace=True)
    clean_df = clean_df[clean_df['PublicationYear'] != 0]
    clean_df = clean_df[clean_df['PublicationYear'] != 9999]

    logging.info('Step 3: Updating incorrect values.')
    clean_df.replace(to_replace="2109", value="2019", inplace=True)

    logging.info('Step 4: adding genre and audience columns.')
    clean_df = build_genre_column(clean_df)
    clean_df = build_audience_column(clean_df)
    
 
    logging.info('Saving output file.')
    output_path = Path(output_file)
    if output_path.suffix == '.csv.gz':
        clean_df.to_csv(output_path, index=False, compression="gzip")
    else:
        clean_df.to_csv(output_path, index=False)
    
    return None


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
    main()