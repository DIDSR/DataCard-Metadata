# Datacard - Metadata Completeness Assessment

This repository contains code for the assessment of metadata Completeness for the DataCard project.
The current itertion of the code takes a metadata csv file and a json metadata reference dictionary as input.
A list of matched, missing, and unexpected data header fields are returned as terminal output.
Visulaizations for field and record completeness can also be produced and saved in the `/output` directory.
The file inputs are currently hard-coded.

**This code is work-in-progress.**

## Repo organization

`dcard_completeness_main.py` - Main python module
`io_utils.py` - Functions for reading files and producing plots
`score_utils.py` - Functions for calculating completeness metrics
`field_matching_utils.py` - Functions for matching dataset field names with required field names

## Usage

The `header_matching_methods` dictionary in `dcard_completeness_main.py` consists of a set of methods that are executed in order.
The value for each method is a tuple in which the first item is a flag to enable/disable the method
and the second item contains any additional parameters needed for that method (or None).
`UA` refers to User-Assisted. Enabling this method will use either fuzzy matching or token matching using a language model
to return likely matches for header fields that could not be automatically matched.
For each such field, the user will receive a prompt to select a field from one of the top N 
most likely options (specified by 'limit').
The token matching option is disabled in this version of the code.

```python
header_matching_methods = {
        'strict':(False,None),
        'dictionary':(True,{'field_dictionary':metadata_reference_dictionary}),
        'soft': (False,None),
        'fuzzy': (False,{'threshold':80}),
        'UA':(False,{'ranking_method':'LM','limit':4})  # 'fuzzy' or 'LM'
    }
```