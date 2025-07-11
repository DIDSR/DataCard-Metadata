import sys
import os
import time
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import scipy.stats as stats
import re
import ast
from scipy.special import rel_entr


def calculate_hellinger_dist(counts_p, counts_q, symmetric=False):
    p = np.asarray(counts_p, dtype=np.float64)
    q = np.asarray(counts_q, dtype=np.float64)

    p /= p.sum()
    q /= q.sum()

    return np.sqrt(np.sum((np.sqrt(p) - np.sqrt(q))**2)) / np.sqrt(2)


def calculate_kl_div(counts_p, counts_q, symmetric=False):
    p = np.asarray(counts_p, dtype=np.float64)
    q = np.asarray(counts_q, dtype=np.float64)

    p /= p.sum()
    q /= q.sum()

    kld_pq = np.sum(rel_entr(p, q))

    if symmetric:
        kld_qp = np.sum(rel_entr(q, p))
        return kld_pq + kld_qp
    else:
        return kld_pq
        

def get_divergence_dfs(df1, df2=None, field_values=None, metric="HD", fill_value=1):

    metric_funcs = {
        "KLD": calculate_kl_div,
        "HD": calculate_hellinger_dist
    }
            
    df1_total_records = len(df1)

    observed_counts1 = df1.value_counts().sort_index()
    original_indices1 = observed_counts1.index

    if field_values is None:
        if df2 is not None:
            df_combined = pd.concat([df1, df2], axis=0, ignore_index=True, join='inner')
            observed_counts_combined = df_combined.value_counts().sort_index()
            field_values = observed_counts_combined.index.values
        else:
            field_values = df1.unique()
            
        
    if field_values is not None and not all(element in original_indices1 for element in field_values):
        if metric == "KLD":
            observed_counts_reindexed1 = observed_counts1.reindex(field_values, fill_value=fill_value)
            observed_counts1 = observed_counts_reindexed1.mask(observed_counts_reindexed1.index.isin(original_indices1), 
                                       observed_counts_reindexed1 + fill_value)
        else:
            observed_counts1 = observed_counts1.reindex(field_values, fill_value=0)

    
    if df2 is not None:
        df2_total_records = len(df2)
        observed_counts2 = df2.value_counts().sort_index()
        original_indices2 = observed_counts2.index

        if field_values is not None and not all(element in original_indices2 for element in field_values):
            if metric == "KLD":
                observed_counts_reindexed2 = observed_counts2.reindex(field_values, fill_value=fill_value)
                observed_counts2 = observed_counts_reindexed2.mask(observed_counts_reindexed2.index.isin(original_indices2), 
                                           observed_counts_reindexed2 + fill_value)
            else:
                observed_counts2 = observed_counts2.reindex(field_values, fill_value=0)
            
        df = pd.DataFrame({'df1': observed_counts1, 'df2': observed_counts2})

        divergence_value = metric_funcs[metric](df['df1'], df['df2'], symmetric=True)

        return divergence_value, {'dist1':observed_counts1/observed_counts1.sum(), 'dist2':observed_counts2/observed_counts2.sum()}
    else:
        num_unique = len(observed_counts1)
        df1_counts_uniform = np.full(num_unique,df1_total_records/num_unique)
        divergence_value = metric_funcs[metric](observed_counts1, df1_counts_uniform, symmetric=False)
        
        return divergence_value, {'dist1':observed_counts1/observed_counts1.sum()}


def get_coverage_df(dataset_df_full, required_fields, available_headers=None, coverage_params=None):


    target_field = coverage_params['target_field']
    assert target_field in available_headers.keys() or target_field in dataset_df_full.columns, f'Target field {target_field} not found in metadata.'

    if available_headers is not None and len(available_headers)>0 and target_field in available_headers.keys():

        drop_columns = [col for col in dataset_df_full.columns if col not in available_headers.values()]
        complete_dataset_df = dataset_df_full.drop(columns=drop_columns)
        
        for col in required_fields:
            if col not in available_headers.keys():
                complete_dataset_df[col] = np.nan
        new_names_dict = {v:k for k,v in available_headers.items()}
        dataset_df_full = complete_dataset_df.rename(columns=new_names_dict)

    empty_rows = dataset_df_full.isna().all(axis=1)
    empty_row_indexes = empty_rows[empty_rows].index.tolist()
    
    if empty_row_indexes:
        first_empty_row_index = empty_row_indexes[0]
        dataset_df = dataset_df_full.iloc[:first_empty_row_index]
    else:
        dataset_df = dataset_df_full
    
    record_num = len(dataset_df[target_field])
    if len(dataset_df[target_field].unique()) > 0.9*record_num:
        print('Coverage cannot be computed')
        return 0

    if coverage_params['fill_na'] is not None:
        data_values = dataset_df[target_field].fillna(coverage_params['fill_na'])
    else:
        data_values = dataset_df[target_field].dropna()

    # If data type is int, attempt to use regex to extract values from text
    if coverage_params['dtype'] == 'int':
        try:
            data_values = data_values.str.extract(r'0*(\d+)', expand=False).astype('int32')
        except:
            data_values = data_values.astype('int32')
        if coverage_params['thresholds'] is not None:
            data_values = data_values[(data_values >= coverage_params['thresholds'][0]) & (data_values <= coverage_params['thresholds'][1])]

    return data_values


def bucket_values(data_values, value_buckets):
    
    buckets = sorted(value_buckets)

    if len(buckets) == 1:
        bin_edges = [-np.inf, np.inf]
        labels = buckets
    else:
        bin_edges = [-np.inf]
        bin_edges.extend([(buckets[i] + buckets[i+1]) / 2 for i in range(len(buckets)-1)])
        bin_edges.append(np.inf)
        labels = buckets
    
    data_values = pd.cut(data_values, bins=bin_edges, labels=labels, include_lowest=True)

    return data_values

    


def coverage_check(dataset_df_full, required_fields, available_headers=None, dataset_df2_full=None, available_headers2=None, coverage_params=None, visualize=False,savefig=False):
    """
    Perform a coverage check for a target field in the metadata.

    Args:
        dataset_df (pd.DataFrame): The dataset as a pandas DataFrame.
        required_fields (list): List of required metadata fields.
        available_headers:
        target_field:

    Returns:
        None
    """
    data_values = get_coverage_df(dataset_df_full, required_fields, available_headers, coverage_params)

    group_values_into_buckets = False
    if 'value_buckets' in coverage_params:
        if coverage_params['value_buckets'] is not None:
            group_values_into_buckets = True

    if group_values_into_buckets:
        data_values = bucket_values(data_values, coverage_params['value_buckets'])

    if dataset_df2_full is not None:
        data_values2 = get_coverage_df(dataset_df2_full, required_fields, available_headers2, coverage_params)
        if group_values_into_buckets:
            data_values2 = bucket_values(data_values2, coverage_params['value_buckets'])
        divergence_value, features = get_divergence_dfs(data_values, data_values2, field_values=coverage_params['field_values'], metric=coverage_params['metric'], fill_value=1)
    else:
        divergence_value, features = get_divergence_dfs(data_values, df2=None, field_values=coverage_params['field_values'], metric=coverage_params['metric'], fill_value=1)

    print(f'Number of records (after cleaning and thresholding): {len(data_values)}')
    print(f"Unique values of {coverage_params['target_field']}: {np.sort(data_values.unique())}")

    if coverage_params['metric'] == 'KLD':
        print(f'Divergence metric: Kullback–Leibler divergence')
    elif coverage_params['metric'] == 'HD':
        print(f'Divergence metric: Hellinger distance')
    else:
        print('Unknown metric')

    if dataset_df2_full is not None:
        print(f'Divergence between Dataset 1 and Dataset 2: {divergence_value}')
    else:
        print(f'Divergence from uniform: {divergence_value}')


    if visualize:
        num_unique = len(data_values.unique())
        if num_unique > 50 and coverage_params['bin_count'] is None:
            print('Too many values to plot.')
            return features
  
        if coverage_params['bin_count'] is not None:
            fig_width = 12 + 0.1*int(coverage_params['bin_count'])
            fig, ax = plt.subplots(1,1,figsize=(fig_width,6))
            data_values.plot(ax=ax,kind='hist',bins=coverage_params['bin_count'], edgecolor='black',
                                                         title=f"{coverage_params['target_field']} Coverage",fontsize=6)
        else:
            fig_width = 12 + 0.2*num_unique
            fig, ax = plt.subplots(1,1,figsize=(fig_width,6))
            observed_counts = data_values.value_counts().sort_index()
            original_indices = observed_counts.index
            if coverage_params['field_values'] is not None and not all(element in original_indices for element in coverage_params['field_values']):
                observed_counts = observed_counts.reindex(coverage_params['field_values'], fill_value=0)
            observed_counts.plot(ax=ax,kind='bar',title=f"Coverage for field: {coverage_params['target_field']}",fontsize=10)
        plt.xticks(rotation=0, fontsize=10)
        plt.yticks(fontsize=10)
        plt.xlabel('Items', fontsize=12)
        plt.ylabel('Count', fontsize=12)
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        for p in ax.patches:
            ax.annotate(str(p.get_height()), (p.get_x() + p.get_width() / 2., p.get_height()),
                        ha='center', va='bottom')
        if savefig:
            timestr = time.strftime("%Y%m%d_%H%M%S")
            fig.savefig('output/Coverage_'+timestr+'.png',bbox_inches='tight',pad_inches=0.1,facecolor='w')
        
    return features
