import os
import time
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

from Coverage.compute_coverage import *


def assign_band(value, bands, labels):
    """Assigns a value to the appropriate band based on defined ranges and returns
    the corresponding label.
    
    :param value: Numeric value to be assigned to a band.
    :type value: float or int
    :param bands: List of tuples defining the lower and upper bounds for each band.
    :type bands: List[tuple]
    :param labels: List of labels corresponding to each band range.
    :type labels: List[str]
    :return: Label of the band that contains the value, or 'Unavailable' if no band matches
    :rtype: str
    
    """
    for i, (low, high) in enumerate(bands):
        if low <= value <= high:
            return labels[i]
    return 'Unavailable'


def consistency_check(dataset_df, required_fields, available_headers, coverage_params_subgroup, coverage_params_target,visualize=True,savefig=False):

    """Performs consistency analysis by examining the distribution of target field values
    across different subgroups, with optional visualization of cross-tabulated results.
    
    :param dataset_df: Dataset dataframe containing the fields to analyze.
    :type dataset_df: pandas.DataFrame
    :param required_fields: List of fields that are required for the analysis.
    :type required_fields: List[str]
    :param available_headers: Dictionary mapping required field names to actual column names in the dataset.
    :type available_headers: dict
    :param coverage_params_subgroup: Dictionary containing parameters for subgroup field analysis including target_field, thresholds, and bin_count.
    :type coverage_params_subgroup: dict
    :param coverage_params_target: Dictionary containing parameters for target field analysis including target_field and optional value_buckets.
    :type coverage_params_target: dict
    :param visualize: Whether to generate visualization plots of the consistency analysis.
    :type visualize: bool
    :param savefig: Whether to save generated plots to file with timestamp.
    :type savefig: bool
    :return: DataFrame containing the consistency analysis results with subgroup, target, and band assignments
    :rtype: pandas.DataFrame
    
    """

    subgroup_values = get_coverage_df(dataset_df, required_fields, available_headers=available_headers, coverage_params=coverage_params_subgroup)

    target_values = get_coverage_df(dataset_df, required_fields, available_headers=available_headers, coverage_params=coverage_params_target)

    group_values_into_buckets = False
    if 'value_buckets' in coverage_params_target:
        if coverage_params_target['value_buckets'] is not None:
            group_values_into_buckets = True
    
    if group_values_into_buckets:
        target_values = bucket_values(target_values, coverage_params_target['value_buckets'])
  
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
