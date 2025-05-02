
from field_matching_utils import *
from io_utils import *
from score_utils import *

import argparse

def main():
    parser = argparse.ArgumentParser(description='Provide dataset metadata file and reference dictionary.')
    parser.add_argument('--data_path', type=str, default=None, help='Path to dataset metadata file')
    parser.add_argument('--reference_path', type=str, default=None, help='Path to metadata reference dictionary')
    parser.add_argument('--cc_level', type=str, default="Core Fields", help='The level at which completeness should be assessed.')
    args = parser.parse_args()

    metadata_reference_path = args.reference_path
    metadata_file_path = args.data_path
    completeness_check_level = args.cc_level
    assert metadata_reference_path is not None, 'Reference dictionary path not specified.'
    assert metadata_file_path is not None, 'Metadata file path not specified.'

    # Create output directory to store visualizations
    os.makedirs('output', exist_ok=True)

    # Load required metadata fields from a json dictionary and retrieve the list of aliases for each field.
    metadata_reference_dictionary = get_dictionary(metadata_reference_path,completeness_check_level)
    field_aliases = get_field_item(metadata_reference_dictionary)
    required_fields = list(field_aliases.keys())

    # Load the dataset metadata
    # This step loads the dataset metadata (a multi-column CSV/XLS file) into a pandas DataFrame.
    # Each column represents a metadata attribute (e.g., 'PatientID', 'Modality'), and each row represents a data point.
    metadata_df = load_metadata_file(metadata_file_path)

    if metadata_df is not None:
        print(f"Assessing completeness for metadata file '{os.path.basename(metadata_file_path)}'")

    """
    Perform dataset-level completeness check
    This checks if the dataset's headers (column names) match the required fields.
    - Missing Headers: Required fields that are not present in the dataset.
    - Unexpected Headers: Fields present in the dataset that are not part of the required fields.

    The field_matching_methods dictionary consists of a set of matching methods that are executed in order.
    The value for each method is a tuple in which the first item is a flag to enable/disable the method
    and the second item contains any additional parameters needed for that method (or None).
    `UA` refers to User-Assisted. Enabling this method will use either fuzzy matching or token matching using a language model
    to return likely matches for header fields that could not be automatically matched.
    For each such field, the user will receive a prompt to select a field from one of the top N most likely options (specified by 'limit').
    The token matching option is disabled in this version of the code.
    """

    field_matching_methods = {
        'strict':(False,None),
        'dictionary':(True,{'field_dictionary':field_aliases}),
        'soft': (False,None),
        'fuzzy': (False,{'threshold':80}),
        'UA':(False,{'ranking_method':'LM','limit':4})  # 'fuzzy' or 'LM'
    }

    if metadata_df is not None and required_fields:
        completeness_report = dataset_level_completeness_check(metadata_df, required_fields, field_matching_methods)

        # Extract missing and unexpected headers for clarity
        available_header_map = completeness_report["available_header_map"]
        missing_headers = completeness_report["missing_headers"]
        unexpected_headers = completeness_report["unexpected_headers"]
        completeness_score = completeness_report["completeness_score"]

        # Show header mapping
        # If there are required fields missing from the dataset, list them.
        if available_header_map:
            print('Required Header\t\tMatched Dataset Header')
            print('---------------------------------------------')
            for k,v in available_header_map.items():
                print('{:<20}\t{:<12}'.format(k,v))
        else:
            print(f"All required fields are missing for {completeness_check_level}.")

        # Step 4: Report Missing Headers
        # If there are required fields missing from the dataset, list them.
        if missing_headers:
            print(f"\nMissing Headers: {missing_headers}\n")
        else:
            print("No missing headers. All required fields are present.")

        # Step 5: Report Unexpected Headers
        # If the dataset contains extra fields not listed in the required fields, list them.
        if unexpected_headers:
            print(f"Unexpected Headers: {unexpected_headers}\n")
        else:
            print("No unexpected headers. All dataset fields are required.")

        # Step 6: Report Completeness Score
        print(f"Completeness Score: {completeness_score:.2f}")

        # Step 7: Perform record-level completeness check
        # This checks individual columns and rows in the metadata file and reports completion information
        record_level_results = record_level_completeness_check(metadata_df, required_fields, available_header_map,visualize=True,savefig=False)
    else:
        # Handle cases where either the dataset or required fields failed to load.
        print("Failed to load dataset or required fields.")

    

if __name__ == "__main__":
    main()