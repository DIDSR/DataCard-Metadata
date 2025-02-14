import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from field_matching_utils import *



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
    }
 
    dataset_headers = dataset_df.columns.tolist()  # Extract the headers from the dataset

    available_header_map = {}

    for method, params in header_matching_methods.items():
        if params[0]:
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
              - 'incomplete_records': A dictionary where each key is the record index and the value is a list of missing fields.
              - 'incomplete_count': The total number of incomplete records.
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
        req_missing_per_column = dataset_df[available_headers.values()].isnull().sum()
        req_columns_with_missing_values = req_missing_per_column[req_missing_per_column>0]

        req_missing_per_column_perc = 100* req_missing_per_column/ total_records
        req_available_per_column_perc = 100 - req_missing_per_column_perc
    
        req_missing_cols_df = pd.DataFrame({
            "Missing Count": req_columns_with_missing_values,
            "Missing Percentage" : (req_columns_with_missing_values / total_records *100).round(2)
        }).sort_values(by="Missing Count", ascending=False)

        req_column_completeness = pd.DataFrame({
            "Available (%)": req_available_per_column_perc,
            "Missing (%)" : req_missing_per_column_perc
        }).sort_values(by="Available (%)", ascending=False)

        complete_dataset_df = dataset_df.copy()
        drop_columns = [col for col in complete_dataset_df.columns if col not in available_headers.values()]
        complete_dataset_df = complete_dataset_df.drop(columns=drop_columns)
        
        for col in required_fields:
            if col not in available_headers.keys():
                complete_dataset_df[col] = np.nan
        new_names_dict = {v:k for k,v in available_headers.items()}
        complete_dataset_df = complete_dataset_df.rename(columns=new_names_dict)
        req_missing_per_column1 = complete_dataset_df.isnull().sum()
        req_columns_with_missing_values1 = req_missing_per_column1[req_missing_per_column1>0]

        req_missing_per_column_perc1 = 100* req_missing_per_column1/ total_records
        req_available_per_column_perc1 = 100 - req_missing_per_column_perc1
    
        req_missing_cols_df1 = pd.DataFrame({
            "Missing Count": req_columns_with_missing_values1,
            "Missing Percentage" : (req_columns_with_missing_values1 / total_records *100).round(2)
        }).sort_values(by="Missing Count", ascending=False)

        req_column_completeness1 = pd.DataFrame({
            "Available (%)": req_available_per_column_perc1,
            "Missing (%)" : req_missing_per_column_perc1
        }).sort_values(by="Available (%)", ascending=False)
        
    
    missing_per_row = dataset_df.isnull().sum(axis=1)
    rows_with_missing_values = missing_per_row[missing_per_row>0]
    
    row_missing_dist = missing_per_row.value_counts().sort_index()
    
    missing_rows_df = pd.DataFrame({
        "Missing Values per Record": row_missing_dist.index,
        "Number of Records" : row_missing_dist.values
    })

    complete_records = total_records - len(rows_with_missing_values)
    complete_records_percentage = 100*complete_records / total_records

    if visualize:

        if savefig:
            timestr = time.strftime("%Y%m%d_%H%M%S")

        fig1,ax1 = plt.subplots(figsize=(16,4))
        column_completeness.plot(ax=ax1,kind='bar', stacked=True, figsize=(12,6), color=['#55CC99','#DD3333'],edgecolor='k')
        plt.title('Overall Column Completeness')
        plt.xlabel('Columns')
        plt.ylabel('Percentage (%)')
        plt.xticks(rotation=45,ha='right')
        plt.legend(['Available (%)', 'Missing (%)'], loc='upper right')
        plt.grid(axis='y', linestyle='--', alpha=0.7)

        if savefig:
            fig1.savefig('output/'+'Overall_Column_Completeness_'+timestr+'.png',bbox_inches='tight',pad_inches=0.1,facecolor='w')

        if available_headers is not None and len(available_headers)>0:
            fig2,ax2 = plt.subplots(figsize=(16,4))
            req_column_completeness.plot(ax=ax2,kind='bar', stacked=True, figsize=(12,6), color=['#5577DD','#DD3333'],edgecolor='k')
            plt.title('Required Column Completeness (Available Columns)')
            plt.xlabel('Columns')
            plt.ylabel('Percentage (%)')
            plt.xticks(rotation=45,ha='right')
            plt.legend(['Available (%)', 'Missing (%)'], loc='upper right')
            plt.grid(axis='y', linestyle='--', alpha=0.7)

            if savefig:
                fig2.savefig('output/'+'Required_Column_Completeness_Available_'+timestr+'.png',bbox_inches='tight',pad_inches=0.1,facecolor='w')

            fig3,ax3 = plt.subplots(figsize=(16,4))
            req_column_completeness1.plot(ax=ax3,kind='bar', stacked=True, figsize=(12,6), color=['#5577DD','#DD3333'],edgecolor='k')
            plt.title('Required Column Completeness (All Required Columns)')
            plt.xlabel('Columns')
            plt.ylabel('Percentage (%)')
            plt.xticks(rotation=45,ha='right')
            plt.legend(['Available (%)', 'Missing (%)'], loc='upper right')
            plt.grid(axis='y', linestyle='--', alpha=0.7)

            if savefig:
                fig3.savefig('output/'+'Required_Column_Completeness_All_'+timestr+'.png',bbox_inches='tight',pad_inches=0.1,facecolor='w')
        
        fig, ax = plt.subplots(1,2,figsize=(16,8))
        colors = plt.cm.Blues(np.linspace(0.1, 0.5, len(row_missing_dist)))
        missing_per_row_perc = (100* row_missing_dist/ len(dataset_df)).round(2)
        labels = [f'{idx} ({pct}%)' for idx, pct in zip(row_missing_dist, missing_per_row_perc)]
        legend_labels = [f'{idx}' for idx in row_missing_dist.index]
        wedges, texts = ax[0].pie(row_missing_dist,labels=labels,
                startangle=90, colors=colors, wedgeprops={'edgecolor':'k'})
        ax[0].legend(wedges, legend_labels, title='Missing field count', loc = 'upper right')
        ax[0].set_title('Record Completeness',fontsize=14)

        columns_with_missing_values_list = [column for column in columns_with_missing_values.index]
        total_records_missing_values = missing_rows_df[missing_rows_df['Missing Values per Record']>0]['Number of Records'].sum()
        report_text = f"""
            **Record and Column Completeness:**
            
            Total records: {total_records}
            
            Columns with missing values: {columns_with_missing_values_list}

            Number of records with at least 1 missing column value: {total_records_missing_values}
        """
        ax[1].text(-0.2,0.8, report_text, fontsize=12, ha='left', va='center', wrap=True)
        ax[1].axis('off')

        if savefig:
            fig.savefig('output/'+'Record_Completeness_and_Summary_'+timestr+'.png',bbox_inches='tight',pad_inches=0.1,facecolor='w')

    # Return both the missing records and the count
    return {
        "missing_rows_stats_df": missing_rows_df,
        "missing_cols_stats_df": missing_cols_df,
        "column_completeness": column_completeness,
        "required_missing_columns":req_missing_cols_df,
        "required_column_completeness": req_column_completeness,
        "complete_records":complete_records,
        "complete_records_percentage": complete_records_percentage
    }