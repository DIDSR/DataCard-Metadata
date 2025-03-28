import os
import time
import pandas as pd
import numpy as np
from field_matching_utils import *
from io_utils import *



def dataset_level_completeness_check(dataset_df, required_fields, header_matching_methods):
    """
    Perform a dataset-level completeness check to verify that the dataset header contains all required fields.

    Args:
        dataset_df (pd.DataFrame): The dataset as a pandas DataFrame.
        required_fields (list): List of required metadata fields.

    Returns:
        dict: A dictionary containing missing headers and unexpected headers.
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

    for method, params in header_matching_methods.items():
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
        if header_matching_methods['UA'][0]:
            matching_function_arguments = {
                'dataset_fields':unmatched_dataset_headers,
                'required_fields': missing_required_headers,
            }
            if header_matching_methods['UA'][1] is not None and isinstance(header_matching_methods['UA'][1], dict):
                matching_function_arguments.update(header_matching_methods['UA'][1])
            matched_header_map = matching_function_map['UA'](**matching_function_arguments)
            for k,v in matched_header_map.items():
                available_header_map.setdefault(k,v)
    
    missing_headers = [field for field in required_fields if field not in available_header_map.keys()]
    unexpected_headers = [field for field in dataset_headers if field not in available_header_map.values()]

    # Report findings
    return {
        "available_header_map": available_header_map,
        "missing_headers": missing_headers,
        "unexpected_headers": unexpected_headers,
        "completeness_score": compute_completeness_score(missing_headers, required_fields)
    }

def compute_completeness_score(missing_headers, required_fields):
    """
    Compute the completeness score based on the presence or absence of required fields.

    Args:
        missing_headers (list): List of required fields missing from the dataset.
        required_fields (list): List of all required metadata fields.

    Returns:
        float: Completeness score (value between 0 and 1).
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
    Perform an image (data) point-level completeness check to verify each record has all required metadata.

    Args:
        dataset_df (pd.DataFrame): The dataset as a pandas DataFrame.
        required_fields (list): List of required metadata fields.

    Returns:
        dict: A dictionary with the following keys:
            - 'total_records': Total number of records
            - 'missing_rows_stats_df': Summary of the number of missing column values per row
            - 'missing_cols_stats_df': Summary of the number of missing row values per clumn
            - 'column_completeness': Completeness of columns available in metadata file,
            - 'required_column_completeness': Completeness of required columns,
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

        # fig, ax = plt.subplots(1,2,figsize=(16,8))
        # colors = plt.cm.Blues(np.linspace(0.1, 0.5, len(row_missing_dist)))
        # missing_per_row_perc = (100* row_missing_dist/ len(dataset_df)).round(2)
        # labels = [f'{idx} ({pct}%)' for idx, pct in zip(row_missing_dist, missing_per_row_perc)]
        # legend_labels = [f'{idx}' for idx in row_missing_dist.index]
        # bins = np.arange(-0.5,np.amax(missing_per_row)+1)
        # counts, bins, patches = ax[0].hist(missing_per_row,bins=bins)
        # bin_centers = (bins[:-1]+bins[1:])/2
        # ax[0].set_xticks(bin_centers)
        # ax[0].set_xlabel('Number of missing fields', fontsize=16)
        # ax[0].set_ylabel('Number of records', fontsize=16)
        # for center, count in zip(bin_centers,counts):
        #     # height = patch.get_height()+1
        #     ax[0].text(center, count+1, f'{int(count)} ({100*count/len(dataset_df):.2f}%)', ha='center', va='bottom', color='k')
        # # ax[0].legend(legend_labels, title='Missing field count', loc = 'upper right')
        # ax[0].set_title('Record Completeness histogram',fontsize=16)

        # colors = plt.cm.Blues(np.linspace(0.1, 0.5, len(row_missing_dist)))
        # missing_per_row_perc = (100* row_missing_dist/ len(dataset_df)).round(2)
        # labels = [f'{idx} ({pct}%)' for idx, pct in zip(row_missing_dist, missing_per_row_perc)]
        # legend_labels = [f'{idx}' for idx in row_missing_dist.index]
        # wedges, texts = ax[1].pie(row_missing_dist,labels=labels,
        #         startangle=90, colors=colors, wedgeprops={'edgecolor':'k'})
        # ax[1].legend(wedges, legend_labels, title='Number of missing fields', fontsize=14, loc = 'upper right')
        # ax[1].set_title('Record Completeness Pie chart',fontsize=16)

        # if savefig:
        #     timestr = time.strftime("%Y%m%d_%H%M%S")
        #     fig.savefig('output/Record Completeness_'+timestr+'.png',bbox_inches='tight',pad_inches=0.1,facecolor='w')


    # Return both the missing records and the count
    return {
        'total_records': total_records,
        'missing_rows_stats_df': missing_rows_df,
        'missing_cols_stats_df': missing_cols_df,
        'column_completeness': column_completeness,
        'required_column_completeness': req_column_completeness,
    }