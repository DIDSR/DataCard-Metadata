import os
import time
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

from Coverage.compute_coverage import *


def assign_band(value, bands, labels):
        for i, (low, high) in enumerate(bands):
            if low <= value <= high:
                return labels[i]
        return 'Unavailable'


def consistency_check(dataset_df, required_fields, available_headers, coverage_params_subgroup, coverage_params_target,visualize=True,savefig=False):
    """
    Perform a consistency check for a target field in the metadata.

    Args:
        dataset_df (pd.DataFrame): The dataset as a pandas DataFrame.
        required_fields (list): List of required metadata fields.
        available_headers:
        target_field:

    Returns:
        None
    """

    subgroup_values = get_coverage_df(dataset_df, required_fields, available_headers=available_headers, coverage_params=coverage_params_subgroup)

    target_values = get_coverage_df(dataset_df, required_fields, available_headers=available_headers, coverage_params=coverage_params_target)
    
    if coverage_params_target['value_buckets'] is not None:
        buckets = sorted(coverage_params_target['value_buckets'])
    
        # Create bin edges at midpoints between buckets
        if len(buckets) == 1:
            bin_edges = [-np.inf, np.inf]
            labels = buckets
        else:
            bin_edges = [-np.inf]
            bin_edges.extend([(buckets[i] + buckets[i+1]) / 2 for i in range(len(buckets)-1)])
            bin_edges.append(np.inf)
            labels = buckets
        
        target_values = pd.cut(target_values, bins=bin_edges, labels=labels, include_lowest=True)
    
    consistency_df = pd.concat([subgroup_values, target_values], axis=1, keys=['Subgroup', 'Target'], join='inner')

    bands = [(i, i+coverage_params_subgroup['bin_count']-1) for i in range(coverage_params_subgroup['thresholds'][0],coverage_params_subgroup['thresholds'][1],coverage_params_subgroup['bin_count'])]
    band_labels = [str(b) for b in bands]
    
    consistency_df['band'] = consistency_df['Subgroup'].apply(lambda x: assign_band(x, bands, band_labels))

    band_counts = consistency_df.groupby(['band', 'Target'], observed=False).size().unstack(fill_value=0)
  
    band_counts_transposed = band_counts.T
    
    if visualize:
        if len(target_values.unique()) > 50:
            print('Too many values to plot.')
            return consistency_df
        # Create grouped bar chart
        fig, ax = plt.subplots(1,1,figsize=(15,10))
        band_counts_transposed.plot(ax=ax,kind='bar', figsize=(10, 4), width=0.8)
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.title(f"{coverage_params_target['target_field']} across {coverage_params_subgroup['target_field']}")
        plt.xlabel(f"{coverage_params_target['target_field']}", fontsize=12)
        plt.ylabel('Count', fontsize=12)
        plt.legend(title='Subgroups', bbox_to_anchor=(1.05, 1), loc='upper left',fontsize=10)
        plt.xticks(rotation=0, fontsize=12)
        plt.yticks(fontsize=12)
        plt.tight_layout()
        plt.show()

        if savefig:
            timestr = time.strftime("%Y%m%d_%H%M%S")
            fig.savefig('output/Consistency_'+timestr+'.png',bbox_inches='tight',pad_inches=0.1,facecolor='w')

    return consistency_df
