import os
import time
import pandas as pd
import numpy as np
from field_matching_utils import *
from io_utils import *



def dataset_level_completeness_check(dataset_df, required_fields, field_matching_methods):

    """
    Perform a dataset-level completeness check to verify that the dataset header contains all required fields.
    
    :param dataset_df: Nested dictionary containing dataset metadata
    :type dataset_df: Dictionary
    :param required_fields: List of required fields
    :type required_fields: List[str]
    :param field_matching_methods: Dictionary with names of field matching methods to be used and parameters for each method
    :type field_matching_methods: Dictionary
    :return: Dictionary containing missing fields and unexpected fields
    :rtype: Dictionary

    """

    matching_function_map = {
        'strict':strict_field_matching,
        'soft': soft_field_matching,
        'dictionary':dictionary_field_matching,
        'fuzzy': fuzzy_field_matching,
        'UA': ranked_field_matching
    }
 
    dataset_headers = dataset_df.columns.tolist()  # Extract the headers from the dataset

    available_header_map = {}

    for method, params in field_matching_methods.items():
        if params[0] and method != 'UA':
            matching_function_arguments = {
                'dataset_fields':dataset_headers,
                'required_fields': required_fields,
            }
            if params[1] is not None and isinstance(params[1], dict):
                matching_function_arguments.update(params[1])
            matched_header_map = matching_function_map.get(method, lambda: "Invalid matching method specified")(**matching_function_arguments)

            for k,v in matched_header_map.items():
                available_header_map.setdefault(k,v)

    # Identify missing and unexpected headers
    missing_required_headers = [field for field in required_fields if field not in available_header_map.keys()]
    unmatched_dataset_headers = [field for field in dataset_headers if field not in available_header_map.values()]

    if missing_required_headers:
        if field_matching_methods['UA'][0]:
            matching_function_arguments = {
                'dataset_fields':unmatched_dataset_headers,
                'required_fields': missing_required_headers,
            }
            if field_matching_methods['UA'][1] is not None and isinstance(field_matching_methods['UA'][1], dict):
                matching_function_arguments.update(field_matching_methods['UA'][1])
            matched_header_map = matching_function_map['UA'](**matching_function_arguments)
            for k,v in matched_header_map.items():
                available_header_map.setdefault(k,v)
    
    missing_headers = [field for field in required_fields if field not in available_header_map.keys()]
    unexpected_headers = [field for field in dataset_headers if field not in available_header_map.values()]

    completeness_report = {
        "available_header_map": available_header_map,
        "missing_headers": missing_headers,
        "unexpected_headers": unexpected_headers,
        "completeness_score": compute_completeness_score(missing_headers, required_fields)
    }

    return completeness_report

def compute_completeness_score(missing_headers, required_fields):

    """
    Compute the completeness score based on the presence or absence of required fields.
    
    :param missing_headers: List of required fields that are missing from the dataset metadata.
    :type missing_headers: List[str]
    :param required_fields: List of all required metadata fields.
    :type required_fields: List[str]

    :return: Score between 0 and 1
    :rtype: float

    """

    total_required = len(required_fields)  # Total number of required fields
    missing_count = len(missing_headers)  # Number of missing fields

    if total_required == 0:
        return 0.0  # Avoid division by zero, no required fields means completeness is zero

    present_count = total_required - missing_count  # Number of fields present
    completeness_score = present_count / total_required
    return completeness_score


def record_level_completeness_check(dataset_df, required_fields, available_headers=None, visualize=False,savefig=False):
    
    """
    Perform a check at the record level to check the metadata availability of each data record.
    Return missing field information for each record.
    
    :param dataset_df: Nested dictionary containing dataset metadata
    :type dataset_df: Dictionary
    :param required_fields: List of all required metadata fields.
    :type required_fields: List[str]
    :param available_headers: Required fields available in metadata. 
        Dictionary with the required field names as keys and the matched dataset field names as values
    :type available_headers: Dictionary
    :param visualize: Flag to plot the record level completeness information in barcharts
    :type visualize: bool
    :param savefig: Flag to save the figures as pngs
    :type savefig: bool

    :return: Dictionary with row and column completeness information
    :rtype: Dictionary

    """

    total_records = len(dataset_df)
    missing_per_column = dataset_df.isnull().sum()
    columns_with_missing_values = missing_per_column[missing_per_column>0]

    missing_per_column_perc = 100* missing_per_column/ total_records
    available_per_column_perc = 100 - missing_per_column_perc

    missing_cols_df = pd.DataFrame({
        "Missing Count": columns_with_missing_values,
        "Missing Percentage" : (columns_with_missing_values / total_records *100).round(2)
    }).sort_values(by="Missing Count", ascending=False)

    column_completeness = pd.DataFrame({
        "Available (%)": available_per_column_perc,
        "Missing (%)" : missing_per_column_perc
    })

    if available_headers is not None and len(available_headers)>0:

        drop_columns = [col for col in dataset_df.columns if col not in available_headers.values()]
        complete_dataset_df = dataset_df.drop(columns=drop_columns)
        
        for col in required_fields:
            if col not in available_headers.keys():
                complete_dataset_df[col] = np.nan
        new_names_dict = {v:k for k,v in available_headers.items()}
        complete_dataset_df = complete_dataset_df.rename(columns=new_names_dict)
        req_missing_per_column = complete_dataset_df.isnull().sum()

        req_missing_per_column_perc = 100* req_missing_per_column/ total_records
        req_available_per_column_perc = 100 - req_missing_per_column_perc

        req_column_completeness = pd.DataFrame({
            "Available (%)": req_available_per_column_perc,
            "Missing (%)" : req_missing_per_column_perc
        }).sort_values(by="Available (%)", ascending=False)
        
    
    if available_headers is not None and len(available_headers)>0:
        missing_per_row = complete_dataset_df.isnull().sum(axis=1)
    else:
        missing_per_row = dataset_df.isnull().sum(axis=1)

    rows_with_missing_values = missing_per_row[missing_per_row>0]
    
    row_missing_dist = missing_per_row.value_counts().sort_index()
    
    missing_rows_df = pd.DataFrame({
        "Missing Values per Record": row_missing_dist.index,
        "Number of Records" : row_missing_dist.values
    })

    complete_records = total_records - len(rows_with_missing_values)
    complete_records_percentage = 100*complete_records / total_records

    print('\n== Record Completeness Summary ==')
    print(f"Total number of records: {total_records}")
    print(f"Number of complete records: {complete_records}")
    print(missing_rows_df)

    if visualize:
        plot_completeness_barchart(column_completeness, available_list = None, plot_title='Completeness of fields present in Metadata', 
                                   plot_colors=['#55CC99','#DD3333'], add_text=True, savefig=savefig)

        if available_headers is not None and len(available_headers)>0:
            plot_completeness_barchart(req_column_completeness, available_list = list(available_headers.keys()), plot_title='Required Field Completeness Summary', 
                                   plot_colors=['#5577DD','#DD3333'], add_text=True, savefig=savefig)


    record_completeness_report = {
        'total_records': total_records,
        'missing_rows_stats_df': missing_rows_df,
        'missing_cols_stats_df': missing_cols_df,
        'column_completeness': column_completeness,
        'required_column_completeness': req_column_completeness,
    }

    return record_completeness_report