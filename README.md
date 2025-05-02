# Datacard - Metadata Completeness Assessment

This repository contains code for the assessment of metadata Completeness for the DataCard project.

> [!NOTE]
> **This code is work-in-progress.**

## Overview

This tool is intended to take a metadata table for a medical imaging dataset and generate a report indicating the
level of Completeness of the metadata. To do so, a modality specific metadata reference dictionary containing required
field information is used along with the metadata file. An outline of this pipeline is given below.

![Completeness Assessment Pipeline](./images/Completeness_Pipeline.png)

The current iteration of the code takes a metadata csv file and a json metadata reference dictionary as input.
A list of matched, missing, and unexpected data header fields are returned as terminal output.
Visualizations for field and record completeness can also be produced and saved in the `/output` directory.
The file inputs are currently hard-coded.


## Installation

The code uses python programming language. A python virtual environment can be created
to install the packages required to run this code. A python venv named `dcard` can be
created using

```
   python3 -m venv .dcard
```

The environment can be activated using
```
   source .dcard/bin/activate
```
After activation, the required packages can be installed inside the environment by running

```
   python3 -m pip install -r requirements.txt
```


## Repository organization

`dcard_completeness_main.py` - Main python module

`io_utils.py` - Functions for reading files and producing plots

`score_utils.py` - Functions for calculating completeness metrics

`field_matching_utils.py` - Functions for matching dataset field names with required field names

## Usage

The tool can be used by running the `dcard_completeness_main.py` python module.

The module accepts 3 arguments:

`--data_path`: Path to dataset metadata file on which completeness assessment needs to be performed

`--reference_path`:  Path to metadata reference dictionary

`--cc_level`: The level at which completeness should be assessed. This argument is used to specify a subgroup within the chosen metadata dictionary.


### Inputs

#### Metadata file

The main input to the tool is a CSV or XLS file containing a set of metadata fields and corresponding values for all records in the database.

A typical metadata file might be organized as follows:

| Patient ID  | Age | Scan Date  | Image ID | Manufacturer  | Resolution (ppi) |
| ----------- | ------ |------- | ------- | -------- | ------ | 
| ABC123  | 29  | 2015-06  | PQ30001  | Hologic  | 500  |
| ABC124  | 52  | 2018-01  | ZD23005  | Siemens  | 700  | 
| ABC124  | 41  | 2018-01  | ZD23005  | Siemens  | 700  | 


#### Metadata dictionary

A metadata dictionary is a json file with metadata fields required for completeness assessment organized in a nested dictionary structure.
Each dictionary is specific to an imaging modality. Examples for modality can be Digital Mammography or Digital Pathology.

Metadata dictionaries follow the three level structure shown below:

```markdown

**Category** (A top level grouping of field classes)
│
├─ **Class** (A group of fields. Completeness is calculated at the Class level.)
│   │
│   ├─ **Field** (A potential header in a metadata file, referred to as a Field, Eg. Patient ID, Image Resolution)
│   │   │
│   │   ├─ description (Text description of the expected information for the field)
│   │   ├─ dtype (The expected data type for the field)
│   │   ├─ aliases (list of possible terms that might also be used to refer to the field)
│   │   └─ checkCoverage (A flag (boolean) to indicate if coverage analysis needs to be done for the data corresponding to the field.)
│   └─ ...
└─ ...

```

### Example dictionary excerpt:

<details open>

<summary> Digital Mammography </summary>

----

$\color{black}{\large{\textbf{- General Fields:}}} \space \color{gray}{\text{\\# The typical set of expected fields for a particular data modality.}}$

$\hspace{0.4in}\color{black}{\large{\textbf{- Core Fields:}}}\space \color{gray}{\text{\\# Required fields over which basic completeness is assessed.}}$

$\hspace{0.8in}\color{black}{\large{\textbf{- Patient ID:}} \space  \\{ } \space \color{gray}{\text{\\# A required metadata field dictionary entry}}$

$\hspace{1.2in}\color{black}{\textbf{- description:}}  \space \color{darkblue}{\text{Unique ID to identify different records from the same patient.}}$

$\hspace{1.2in}\color{black}{\textbf{- dtype:}} \space \color{darkblue}{\text{string}}$

$\hspace{1.2in}\color{black}{\textbf{- aliases:}} \space \color{darkblue}{\text{[Patient Identifier, Unique Patient ID, DICOM Patient ID]}}$

$\hspace{1.2in}\color{black}{\textbf{- checkCoverage:}} \space \color{darkblue}{\text{False}}$

$\hspace{0.8in}\color{black}{\large{\\}}}$


$\hspace{0.8in}\color{black}{\large{\textbf{- Patient Birth Date/Age:}} \space  \\{ }$


$\hspace{1.2in}\color{black}{\textbf{- description:}}  \space \color{darkblue}{\text{Birth date or age of patient}}$

$\hspace{1.2in}\color{black}{\textbf{- dtype:}} \space \color{darkblue}{\text{string}}$

$\hspace{1.2in}\color{black}{\textbf{- aliases:}} \space \color{darkblue}{\text{[Birth Date, Date of Birth, DOB, Age, Patient Age, Patient's Age, Age at dx]}}$

$\hspace{1.2in}\color{black}{\textbf{- checkCoverage:}} \space \color{darkblue}{\text{True}}$

$\hspace{0.8in}\color{black}{\large{\\}}}$


$\hspace{0.8in}\color{black}{\large{\textbf{- Image Resolution:}} \space \\{ }$

$\hspace{1.2in}\color{black}{\textbf{- description:}}  \space \color{darkblue}{\text{The resolution of the image, typically in pixels-per-inch}}$

$\hspace{1.2in}\color{black}{\textbf{- dtype:}} \space \color{darkblue}{\text{int}}$

$\hspace{1.2in}\color{black}{\textbf{- aliases:}} \space \color{darkblue}{\text{[Resolution, PPI, Pixels per inch]}}$

$\hspace{1.2in}\color{black}{\textbf{- checkCoverage:}} \space \color{darkblue}{\text{True}}$

$\hspace{0.8in}\color{black}{\large{\\}}}$

$\hspace{1.2in}\color{black}{\textbf{...}}$


$\hspace{0.4in}\color{black}{\large{\textbf{- Additional Fields:}}}\space \color{gray}{\text{\\# Typically available fields that are not part of basic completeness assessment.}}$

$\hspace{0.8in}\color{black}{\large{\textbf{- Photometric Interpretation:}}\space \\{ }$

$\hspace{1.2in}\color{black}{\textbf{- description:}} \space \color{darkblue}{\text{Intended interpretation of the image pixel data (Monochrome 1 or Monochrome 2)}}$

$\hspace{1.2in}\color{black}{\textbf{- dtype:}} \space \color{darkblue}{\text{string}}$

$\hspace{1.2in}\color{black}{\textbf{- aliases:}}  \space \color{darkblue}{\text{[]}}$

$\hspace{1.2in}\color{black}{\textbf{- checkCoverage:}} \space \color{darkblue}{\text{False}}$

$\hspace{0.8in}\color{black}{\large{\\}}}$

$\hspace{1.2in}\color{black}{\large{...}}$



$\color{black}{\large{\textbf{- Modality Specific Fields:}}}\space \color{gray}{\text{\\# Groups of fields associated with different sub-modalities.}}$

$\hspace{0.4in}\color{black}{\large{\textbf{- DBT:}}}\space \color{gray}{\text{\\# Fields found in Digital Breast Tomosynthesis data.}}$

$\hspace{0.8in}\color{black}{\large{\textbf{- Projection Views:}}\space \\{ }$

$\hspace{1.2in}\color{black}{\textbf{- description:}}\space \color{darkblue}{\text{Number of projection views used for the DBT acquisition}}$

$\hspace{1.2in}\color{black}{\textbf{- dtype:}} \space \color{darkblue}{\text{int}}$

$\hspace{1.2in}\color{black}{\textbf{- aliases:}} \space \color{darkblue}{\text{[Projections, DBT Projections, DICOM Patient ID]}}$

$\hspace{1.2in}\color{black}{\textbf{- checkCoverage:}} \space \color{darkblue}{\text{True}}$

$\hspace{0.8in}\color{black}{\large{\\}}}$

$\hspace{1.2in}\color{black}{\large{...}}$

$\hspace{0.8in}\color{black}{\large{...}}$


$\color{black}{\large{\textbf{- Task Specific Fields:}}}\space \color{gray}{\text{\\# Groups of fields associated with different target tasks.}}$

$\hspace{0.4in}\color{black}{\large{\textbf{- Density Estimation:}}}\space \color{gray}{\text{\\# Fields required for breast density estimation task.}}$

$\hspace{0.8in}\color{black}{\large{\textbf{- Breast Density:}}\space \\{ }$

$\hspace{1.2in}\color{black}{\textbf{- description:}}\space \color{darkblue}{\text{Breast density expressed as a numeric value or ACR category}}$

$\hspace{1.2in}\color{black}{\textbf{- dtype:}} \space \color{darkblue}{\text{string}}$

$\hspace{1.2in}\color{black}{\textbf{- aliases:}} \space \color{darkblue}{\text{[Density, Breast Composition, ACR, ACR Value]}}$

$\hspace{1.2in}\color{black}{\textbf{- checkCoverage:}} \space \color{darkblue}{\text{True}}$

$\hspace{1.2in}\color{black}{\large{\\}}}$

$\hspace{1.2in}\color{black}{\large{...}}$

$\hspace{0.8in}\color{black}{\large{...}}$

-----

</details>

Choosing a subgroup using the `--cc_level` parameter will evaluate completeness with respect to all the fields nested within that subgroup. The default value for this argument is `None` which uses all the fields inside the dictionary.

Besides dictionary-based matching, there are some other additional experimental matching methods implemented in this framework. The methods can be used by modifying the flags in the `header_matching_methods` dictionary in `dcard_completeness_main.py`.

The `header_matching_methods` dictionary consists of a set of methods that are executed in order.
The value for each method is a tuple in which the first item is a flag to enable/disable the method
and the second item contains any additional parameters needed for that method (or None).
`UA` refers to User-Assisted. Enabling this method will use either fuzzy matching or token matching using a language model
to return likely matches for header fields that could not be automatically matched.
For each such field, the user will receive a prompt to select a field from one of the top N 
most likely options (specified by 'limit').

```python
header_matching_methods = {
        'strict':(False,None),
        'dictionary':(True,{'field_dictionary':metadata_reference_dictionary}),
        'soft': (False,None),
        'fuzzy': (False,{'threshold':80}),
        'UA':(False,{'ranking_method':'LM','limit':4})  # 'fuzzy' or 'LM'
    }
```

### Output

The main outputs of dcard-completeness are completeness reports returned by the functions `dataset_level_completeness_check` and `record_level_completeness_check`.

`dataset_level_completeness_check` returns a dictionary with available, missing, and unexpected headers in a metadata file.

`record_level_completeness_check` returns record-wise and field-wise completion statistics of metadata field values in a metadata file.

The main script also outputs text in the terminal window and a set of completeness plots which are saved in the `/output` directory.

Given below is the terminal output for the VinDr-Mammo `metadata.csv` file using the `dm_metadata_dictionary.json` dictionary and performing assessment for the **Core Fields**.

```
Assessing completeness for metadata file 'metadata.csv'
Required Header         Matched Dataset Header
---------------------------------------------
Patient Birth Date/Age  Patient's Age
Breast Orientation      View Position
Laterality              Image Laterality
Image Dimension         Rows        
Pixel Spacing           Imager Pixel Spacing
Manufacturer            Manufacturer
Manufacturer/Model      Manufacturer's Model Name

Missing Headers: ['Patient ID', 'Patient Sex', 'History/Prior', 'Race', 'Ethnicity', 'History/Family', 'Marital status', 'ZIP Code', 'Study ID', 'Study Date', 'Study Time', 'Modality', 'Image Type', 'Image ID', 'Resolution', 'File Format', 'Compression Type', 'Bits Stored', 'Manufacturer/Year', 'Manufacturer/Regulatory']

Unexpected Headers: ['SOP Instance UID', 'Series Instance UID', 'SOP Instance UID.1', 'Photometric Interpretation', 'Columns', 'Pixel Spacing', 'Pixel Padding Value', 'Pixel Padding Range Limit', 'Window Center', 'Window Width', 'Rescale Intercept', 'Rescale Slope', 'Rescale Type', 'Window Center & Width Explanation']

Completeness Score: 0.26

== Record Completeness Summary ==
Total number of records: 20000
Number of complete records: 0
   Missing Values per Record  Number of Records
0                         20              17740
1                         21               2260
```
![Required_Field_Completeness_Summary_VinDrMammo](./images/Required_Field_Completeness_Summary_VinDrMammo.png)

![Available_Field_Completeness_VinDrMammo](./images/Available_Field_Completeness_VinDrMammo.png)