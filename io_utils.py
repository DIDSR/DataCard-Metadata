import time
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import json
import re
import warnings
import numpy as np
import os
import pandas as pd
# Functions for metadata file and dictionary I/O

def load_metadata_file(file_path=None,sep=None):
    """
    Read a metadata file saved in a standard format.

    Args:
        file_path (str): Path to the file.

    Returns:
        pd.DataFrame: Loaded metadata file as a DataFrame.
    """
    if file_path is None:
        file_path = input("Enter the full path to the file (e.g., '/path/to/file.csv'): ").strip("\'\"")

    assert os.path.exists(file_path), "File not found."
    
    meta_file_type = file_path.split('.')[-1]
    # To include a new metadata file type, add the file extension as a key to the function map
    # and as the value add the name of the function which will open the metadata file of the new type
    # and return a pandas dataframe with the metadata
    function_map = {
        'csv' : load_dataset_csv,
        'json': load_json,
        'dicom': load_dicom
    }
    function_args = {
        'file_path':file_path,
    }
    if sep is not None:
        function_args['sep']=sep
    df_metadata = function_map.get(meta_file_type, lambda: "Invalid metadata file type.")(**function_args)

    return df_metadata


def load_dataset_csv(file_path,sep=','):
    """
    Load a CSV file containing the dataset metadata.

    Args:
        file_path (str): Path to the CSV file.

    Returns:
        pd.DataFrame: Loaded CSV as a DataFrame.
    """
    try:
        data = pd.read_csv(file_path,sep=sep)
        return data
    except Exception as e:
        print(f"Error loading dataset CSV: {e}")
        return None


def load_json(file_path):
    """
    To-Do: Add conversion to pd dataframe
    Load a JSON file from the provided path and return a dictionary or list.

    Args:
        file_path (str): Path to the JSON file.

    Returns:
        dict or list: Parsed JSON content.
        None: If the file cannot be processed.
    """
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"Error loading JSON: {e}")
        return None
        
def load_dicom(file_path):
    """
    ?? This will load dicom metadata for a single data file/point.
    To-Do:  (1) Output pd dataframe
            (2) Add parent function to loop over multiple dicom files in a directory and aggregate metadata
            into a dataset level dataframe
    Load a DICOM file from the provided path and extract metadata into a dictionary.

    Args:
        file_path (str): Path to the DICOM file.

    Returns:
        dict: Metadata extracted from the DICOM file.
        None: If the file cannot be processed.
    """
    try:
        dicom_data = pydicom.dcmread(file_path)
        metadata = {elem.tag: elem.value for elem in dicom_data}
        return metadata
    except Exception as e:
        print(f"Error loading DICOM: {e}")
        return None

def get_required_metadata(file_path=None):
    """
    Load the required metadata fields from a CSV file provided by the user.

    Returns:
        list: List of required metadata fields.
    """
    if file_path is None:
        file_path = input("Enter the full path to the file containing required metadata headers (e.g., '/path/to/file.csv'): ").strip("\'\"")

    required_fields = load_required_fields_csv(file_path)

    if required_fields is None or len(required_fields) == 0:
        print("Failed to load the required metadata fields file or the file is empty.")
        return []

    # print(f"Required fields: {required_fields}")
    return required_fields

def load_required_fields_csv(file_path):
    """
    Load a CSV file containing the list of required fields.

    To-Do: This function needs to be made more general so that it can
    load required fields from a structured required metadata file

    Args:
        file_path (str): Path to the CSV file.

    Returns:
        list: List of required metadata fields.
    """
    try:
        data = pd.read_csv(file_path, header=None)  # No header expected
        return data.iloc[:, 0].dropna().tolist()  # Extract the first column as a list
    except Exception as e:
        print(f"Error loading required fields CSV: {e}")
        return None

def flatten_dictionary(nested_dict):
    """
    Flattens a nested dictionary structure.
    Assumes that all keys at all levels are unique!!
    """
    items = []
    for key, value in nested_dict.items():
        if isinstance(value, dict):
            items.extend(flatten_dictionary(value).items())
        else:
            items.append((key, value))
    return dict(items)
    

def get_dictionary(path, target_key=None, flatten=False):
    """
    Load a json file containing a nested-dicitonary structure with unique keys.
    and return the value corresponding to the target key.

    Args:
        path (str): Path to the json file.
        target_key: Key of interest

    Returns:
        dictionary: Dictionary of items.
    """
    d = load_json(path)

    if target_key is not None:
        key_path = find_key_path(d, target_key)

        if key_path is not None:
            for key in key_path:
                if isinstance(d, dict) and key in d:
                    d = d[key]
        else:
            print('Key not found. Returning full dictionary')
    else:
        print('No key specified. Returning full dictionary')

    if flatten:
        d = flatten_dictionary(d)
        
    return d 


def find_key_path(d, target_key=None, key_path=None):
    
    if key_path is None:
        key_path = []
    
    for key, value in d.items():
        new_path = key_path + [key]

        if key == target_key:
            return new_path

        if isinstance(value, dict):
            result = find_key_path(value, target_key, new_path)
            if result:
                return result
    return None

def plot_completeness_barchart(df_plot, available_list = None, plot_title='Completeness', plot_colors=['#5577DD','#DD3333'], add_text=True, savefig=False):
    fig,ax = plt.subplots(figsize=(16,4))
    df_plot.plot(ax=ax,kind='bar', stacked=True, figsize=(12,6), color=plot_colors,edgecolor='k')
    if add_text:
        add_text_sbarchart(ax, df_plot, fontsize=8)
    plt.title(plot_title)
    plt.xlabel('Columns')
    plt.ylabel('Percentage (%)')
    plt.xticks(rotation=45,ha='right')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    if available_list is not None:
        for i, abar in enumerate(ax.containers[1]):
            tick_label = ax.get_xticklabels()[i].get_text()
            if tick_label not in available_list:
                abar.set_color('#FFFFFF')
                abar.set_edgecolor('k')
                abar.set_hatch('//')
        # Custom legend elements needed
        legend_patches = [
            mpatches.Patch(color=plot_colors[0], label = 'Available (%)'),
            mpatches.Patch(color=plot_colors[1], label = 'Unavailable (%)'),
            mpatches.Patch(facecolor='#FFFFFF', edgecolor='k', hatch = '//', label = 'Header Missing')
        ]
        plt.legend(handles=legend_patches, loc='upper right', facecolor='white', framealpha=1)
    else:
        plt.legend(['Available (%)', 'Unavailable (%)'], loc='upper right', facecolor='white', framealpha=1)
    
    if savefig:
        timestr = time.strftime("%Y%m%d_%H%M%S")
        fig.savefig('output/'+plot_title+'_'+timestr+'.png',bbox_inches='tight',pad_inches=0.1,facecolor='w')

    return 0
    


def add_text_sbarchart(ax, df_plot, fontsize):
    bars = ax.patches
    bar_width = bars[0].get_width()

    for i, (index, row) in enumerate(df_plot.iterrows()):
        avail = row.iloc[0]
        missing = row.iloc[1]
        x_pos = i

        if not (pd.isna(avail) or pd.isna(missing)):
            if avail > 0:
                ax.text(x_pos, avail/2, f'{avail:.1f}%', ha='center', va='center', rotation=90, color='white', fontsize=fontsize)
            if missing > 0:
                ax.text(x_pos, avail + (missing/2), f'{missing:.1f}%', ha='center', va='center', rotation=90, color='white', fontsize=fontsize)
    return 0