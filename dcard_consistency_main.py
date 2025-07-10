import argparse
import os

from Completeness import *
from Coverage import *
from Consistency import * 


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

        # Show header mapping
        # If there are required fields missing from the dataset, list them.
        if available_header_map:
            print('Required Header\t\tMatched Dataset Header')
            print('---------------------------------------------')
            for k,v in available_header_map.items():
                print('{:<20}\t{:<12}'.format(k,v))
        else:
            print(f"All required fields are missing for {completeness_check_level}.")
    else:
        # Handle cases where either the dataset or required fields failed to load.
        print("Failed to load dataset or required fields.")


    """
    Perform coverage check for a specified field.

    The coverage_params dictionary consists of the required parameters for the coverage check:
    
        - target_field : The metadata field for which coverage will be computed
        - field_values : All possible values for the target field. If set to None, field_values will be generated from the unique values of the target_field in the metadata.
        - dtype (Optional): 'str' for string or 'int' for integer type. Needed along with regex to extract data values from metadata field item strings
        - value_buckets (Optional): For numeric variables, a list of buckets to group values into before computing consistency
        - metric: 'KLD' for Kullback–Leibler divergence or 'HD' for Hellinger distance
        - fill_na (Optional): Fill NA values in target field with a specific value. Set to 'None' to drop all NA values
        - thresholds (Optional): For numeric variables, only compute coverage within a specified range of values. Eg: [10, 80]
        - bin_count (Optional): For numeric variables, number of bins to generate a histogram plot
    """
    
    coverage_params_subgroup = {
        'target_field': "Patient Birth Date/Age",
        'field_values': None,
        'dtype': 'int',
        'metric': 'HD',
        'fill_na': None,
        'thresholds': [11, 100],
        'bin_count': 10,
    }

    coverage_params_target = {
        'target_field': "mpp",
        'field_values': None,
        'dtype': 'str',
        'value_buckets': [0.25, 0.5],
        'metric': 'HD',
        'fill_na': None,
        'thresholds': None,
        'bin_count': None,
    }


    print(f"\n\nConsistency Information: {coverage_params_target['target_field']} for subgroups of {coverage_params_subgroup['target_field']}")

    f = consistency_check(metadata_df, required_fields, available_headers=available_header_map, 
                        coverage_params_subgroup=coverage_params_subgroup, coverage_params_target=coverage_params_target,
                        visualize=True,savefig=True)             
    

if __name__ == "__main__":
    main()