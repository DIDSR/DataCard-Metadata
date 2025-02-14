from rapidfuzz import fuzz, process
import re
import warnings

def clean_string(s):
    return re.sub(f'[^a-zA-Z0-9 ]',' ',s).lower()

def strict_field_matching(dataset_fields, required_fields):
    field_mappings = {}
    for field in required_fields:
        if field in dataset_fields:
            field_mappings[field] = field
    return field_mappings

def soft_field_matching(dataset_fields, required_fields):
    cleaned_dataset_fields = [(clean_string(item), item) for item in dataset_fields]
    field_mappings = {}
    for field in required_fields:
        cleaned_field = clean_string(field)
        for cleaned_dataset_field, dataset_field in cleaned_dataset_fields:
            if cleaned_field in cleaned_dataset_field:
                field_mappings[field] = dataset_field
    return field_mappings

def dictionary_field_matching(dataset_fields, required_fields, field_dictionary=None, soft_matching=True):

    field_mappings = {}

    dataset_fields_cleaned = [(clean_string(item), item) for item in dataset_fields]
    
    if field_dictionary is not None:     
        for field in required_fields:
            if field in field_dictionary:
                possible_matches = field_dictionary[field]
                possible_matches.append(field)
                possible_matches_cleaned = [clean_string(item) for item in possible_matches]
                match = next((header for clean_header,header in dataset_fields_cleaned if clean_header in possible_matches_cleaned), None)
                if match:
                    field_mappings[field] = match
    else:
        warnings.warn("Metadata field mapping dictionary path not provided")
        
    return field_mappings

def fuzzy_field_matching(dataset_fields, required_fields, similarity_threshold=70):
        field_mappings = {}
    
        # Perform fuzzy matching
        for required_field in required_fields:
            # Find the best match for each required field in dataset headers
            result = process.extractOne(required_field, dataset_fields, scorer=fuzz.ratio)
            if result is not None:
                match, score, _ = result  # Unpack the match, score, and additional data
                if score >= similarity_threshold:
                    field_mappings[required_field] = match
    
        return field_mappings
