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
    """Reads a metadata file into a pandas dataframe. Automatically infers filetype from extension.
    Works with CSV, XLS, and XLSX files.

    :param file_path: Path to metadata file, defaults to None which prompts user to enter file path.
    :type file_path: str
    :param sep: Field separator in metadata file, defaults to None
    :type sep: str
    :return: Pandas dataframe with the loaded metadata
    :rtype: pd.DataFrame

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
        'xls' : load_dataset_xls,
        'xlsx' : load_dataset_xls,
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
    
    :param file_path: Path to metadata file
    :type file_path: str
    :param sep: Field separator in metadata file, defaults to ','
    :type sep: str
    :return: Pandas dataframe with the loaded metadata
    :rtype: pd.DataFrame

    """

    try:
        data = pd.read_csv(file_path,sep=sep)
        return data
    except Exception as e:
        print(f"Error loading dataset CSV: {e}")
        return None


def load_json(file_path):
    """
    Load a JSON file from the provided path
    
    :param file_path: Path to json file
    :type file_path: str

    :return: Parsed JSON data or None
    :rtype: JSON object

    """

    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"Error loading JSON: {e}")
        return None
        

def load_dataset_xls(file_path):

    """
    Load an xls/xlsx file containing the dataset metadata.
    
    :param file_path: Path to metadata file
    :type file_path: str
    :return: Pandas dataframe with the loaded metadata
    :rtype: pd.DataFrame

    """

    try:
        data = pd.read_excel(file_path)
        return data
    except Exception as e:
        print(f"Error loading dataset XLS: {e}")
        return None


def get_field_item(metadata_dictionary,item_key="aliases"):
    """
    For an input metadata dictionary where each top level key is a field name,
    get the specified item values for each field. By default, the list of aliases of each field is retrieved.
    Return a dictionary with the field names as keys and the corresponding items as values.
    
    :param metadata_dictionary: Metadata dictionary object
    :type metadata_dictionary: Dictionary
    :param item_key: Key name for the item to be retrieved
    :type item_key: str
    :return: Dictionary with the field names as keys and the specified items as values
    :rtype field_item_dict: Dictionary

    """

    field_item_dict = {}
    for k,v in metadata_dictionary.items():
        assert item_key in v.keys(), "Specified item not found in metadata dictionary"
        field_item_dict[k] = v[item_key]
    return field_item_dict


def get_dictionary(path, target_key=None):

    """
    Load a python dictionary structure from a json file.
    If a target key is provided, the nested dictionary structure is traversed until the target key is found.
    The value corresponding to the target key, which should be a dictionary, is returned.
    
    :param path: Path to a python dictionary stored in a json file.
    :type path: str
    :param target_key: Dictionary key to retrieve the required metadata dictionary from the input nexted dictionary
    :type target_key: str
    :return: Target dictionary
    :rtype d: dictionary

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
        
    return d 


def find_key_path(d, target_key=None, key_path=None):

    """
    Recursively searches for a target key in a nested dicitonary.
    Returns the path to the first instance of the key as a list.
    
    :param d: Nested dictionary
    :type d: dictionary
    :param target_key: Dictionary key
    :type target_key: str
    :param key_path: Partial path to target key used for recursion, defaults to None
    :type key_path: List[str]
    :return: Full path to target key
    :rtype key_path: List[str]

    """
    
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

    """
    Plot completeness visualization barchart from dataframe
    
    :param df_plot: A matplotlib axis object of the barchart on which to plot the text labels
    :type df_plot:  pd.DataFrame
    :param available_list: List of available headers
    :type available_list: List[str]
    :param plot_title: Title for plot figure
    :type plot_title: str
    :param plot_colors: The two colors to be used in the plot to represent 'Available' and 'Unavailable'.
        Provided as a list of color hex codes.
    :type plot_colors: List[str]
    :param add_text: Flag to add text with completeness levels inside the bars of the chart.
    :type add_text: bool
    :param savefig: Flag to save the plot as a png.
    :type add_text: bool
    :return: 0
    :rtype: int

    """

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
    


def add_text_sbarchart(ax, df_plot, fontsize=8):
    """
    Add text labels inside the bars of a completeness visualization barchart
    
    :param ax: A matplotlib axis object of the barchart on which to plot the text labels
    :type ax: Axes
    :param df_plot: Pandas dataframe with the data for plotting
    :type df_plot: pd.DataFrame
    :param fontsize: Fontsize for the text labels
    :type fontsize: int
    :return: 0
    :rtype: int

    """
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