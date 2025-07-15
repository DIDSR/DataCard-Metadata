import os
import numpy as np
from rapidfuzz import fuzz, process
from sentence_transformers import SentenceTransformer, util
import re
import warnings

def clean_string(s):
    """Cleans an input string by replacing all non-alphanumeric characters with "space".

    :param s: Input string
    :type s: str
    :return: Cleaned string
    :rtype: str
    """
    return re.sub(f'[^a-zA-Z0-9 ]',' ',s).lower()

def strict_field_matching(dataset_fields, required_fields):
    """
    Given lists of required fields and dataset fields, returns a mapping from
    each required field to a dataset field if the required field name is found 
    in the dataset field name.

    :param dataset_fields: Header fields present in dataset metadata.
    :type dataset_fields: List[str]
    :param required_fields: Fields of interest.
    :type required_fields: List[str]
    :return: Dictionary with required_fields present in dataset_fields as keys and the corresponding dataset fields as values
    :rtype: Dictionary

    """
    field_mappings = {}
    for field in required_fields:
        if field in dataset_fields:
            field_mappings[field] = field
    return field_mappings

def soft_field_matching(dataset_fields, required_fields):
    """
    Given lists of required fields and dataset fields, returns a mapping from
    each required field to a dataset field if the cleaned required field name is found 
    in the cleaned dataset field name.
    
    :param dataset_fields: Header fields present in dataset metadata.
    :type dataset_fields: List[str]
    :param required_fields: Fields of interest.
    :type required_fields: List[str]
    :return: Dictionary with required_fields present in dataset_fields as keys and the corresponding dataset fields as values
    :rtype: Dictionary

    """
    cleaned_dataset_fields = [(clean_string(item), item) for item in dataset_fields]
    field_mappings = {}
    for field in required_fields:
        cleaned_field = clean_string(field)
        for cleaned_dataset_field, dataset_field in cleaned_dataset_fields:
            if cleaned_field in cleaned_dataset_field:
                field_mappings[field] = dataset_field
    return field_mappings

def dictionary_field_matching(dataset_fields, required_fields, field_dictionary=None):

    """
    Given lists of required fields and dataset fields, returns a mapping from
    each required field to a dataset field if the required field name is found 
    in the dataset field name. If a field alias dictionary is provided, all cleaned
    aliases for each required field are checked against each dataset field to
    find possible matches.

    :param dataset_fields: Header fields present in dataset metadata.
    :type dataset_fields: List[str]
    :param required_fields: Fields of interest.
    :type required_fields: List[str]
    :param field_dictionary: A dictionary with the required_fields as keys and a list of common variations for each required field as values.
    :type field_dictionary: dict[str]
    :return: Dictionary with required_fields present in dataset_fields as keys and the corresponding dataset fields as values
    :rtype: dict[str]

    """
    
    if field_dictionary is not None:
        field_mappings = {}

        dataset_fields_cleaned = [(clean_string(item), item) for item in dataset_fields]     

        for field in required_fields:
            if field in field_dictionary:
                possible_matches = field_dictionary[field]
                possible_matches.append(field)
                possible_matches_cleaned = [clean_string(item) for item in possible_matches]
                match = next((header for clean_header,header in dataset_fields_cleaned if clean_header in possible_matches_cleaned), None)
                if match:
                    field_mappings[field] = match
    else:
        warnings.warn("Metadata field mapping dictionary path not provided.\nReturning strict matching results")
        field_mappings = strict_field_matching(dataset_fields, required_fields)
        
    return field_mappings

def fuzzy_field_matching(dataset_fields, required_fields, similarity_threshold=70):

    """Given lists of required fields and dataset fields, returns a mapping from
    each required field to a dataset field using fuzzy scoring.
    
    :param dataset_fields: Header fields present in dataset metadata.
    :type dataset_fields: List[str]
    :param required_fields: Fields of interest.
    :type required_fields: List[str]
    :param similarity_threshold: Fuzzy score threshold which determines if the match returned through fuzzy matching is acceptable or not.
    :type similarity_threshold: int
    :return: Dictionary with required_fields present in dataset_fields as keys and the corresponding dataset fields as values
    :rtype: Dictionary

    """

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



def get_fuzzy_matches(dataset_fields, required_fields, limit = 5):

    
    """Given lists of required fields and dataset fields, returns the top N
    matches from dataset fields for each required field using fuzzy scoring

    :param dataset_fields: Header fields present in dataset metadata.
    :type dataset_fields: List[str]
    :param required_fields: Fields of interest.
    :type required_fields: List[str]
    :param limit: Number of matches to return
    :type limit: int
    :return: Dictionary with required_fields as keys and the N most similar dataset_fields along with similarity scores as values
    :rtype: Dictionary
    """

    matches = {}

    for required_field in required_fields:
        results = process.extract(required_field, dataset_fields, scorer=fuzz.ratio, limit=limit)
        matches[required_field] = [(field_name, sim_score) for field_name, sim_score, _ in results]

    return matches

def get_LM_matches(dataset_fields, required_fields, limit = 5):

    """Given lists of required fields and dataset fields, returns the top N
    matches from dataset fields for each required field using cosine-similarity
    score calculated on SentenceTransformer embeddings for the fields.
    
    :param dataset_fields: Header fields present in dataset metadata.
    :type dataset_fields: List[str]
    :param required_fields: Fields of interest.
    :type required_fields: List[str]
    :param limit: Number of matches to return
    :type limit: int
    :return: Dictionary with required_fields as keys and the N most similar dataset_fields along with similarity scores as values
    :rtype: Dictionary

    """
    try:
        model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        matches = {}
    
        dataset_embeddings = model.encode(dataset_fields, convert_to_tensor=True)
        required_embeddings = model.encode(required_fields, convert_to_tensor=True)
    
        # Calculate similarity scores and determine matches
        for idx, required_field in enumerate(required_fields):
            similarities = util.pytorch_cos_sim(required_embeddings[idx], dataset_embeddings).cpu().numpy()
            top_n = np.argpartition(similarities[0], -limit)[-limit:]
            top_n = top_n[np.argsort(similarities[0][top_n])]
            top_n = top_n[::-1]
            results = []
            for i, sim_idx in enumerate(top_n):
                sim = float(similarities[0][sim_idx])
                results.append((dataset_fields[sim_idx],100*float(sim)))
            matches[required_field] = results
            
    except Exception as e:
        print(f'Could not load LM. Using fuzzy matching. Error {e}')

        matches = get_fuzzy_matches(dataset_fields, required_fields, limit = limit)

        return matches

    return matches

def ranked_field_matching(dataset_fields, required_fields, ranking_method='fuzzy', limit = 5):

    """Given lists of required fields and dataset fields, performs
    user-assisted field matching. For each required field, the top N
    matches found from dataset fields using the method specified by ranking_method 
    is provided to the user for selection.
    
    :param dataset_fields: Header fields present in dataset metadata.
    :type dataset_fields: List[str]
    :param required_fields: Fields of interest.
    :type required_fields: List[str]
    :param ranking_method: Specify the ranking method, 'fuzzy' or 'LM' (Language Model)
    :type ranking_method: str
    :param limit: Number of matches to return
    :type limit: int
    :return: Dictionary with required_fields present in dataset_fields as keys and the corresponding dataset fields as values
    :rtype: Dictionary

    """

    ranking_function_map = {
        'fuzzy':get_fuzzy_matches,
        'LM': get_LM_matches,
    }

    ranking_function_arguments = {
        'dataset_fields':dataset_fields,
        'required_fields': required_fields,
        'limit':limit
    }

    print('Using user-assisted ranked matching for umatched headers.')
    if ranking_method == 'fuzzy':
        print('Method: fuzzy matching.')
    else:
        print('Method: sentence transformer.')

    ranked_header_maps = ranking_function_map.get(ranking_method, lambda: "Invalid matching method specified")(**ranking_function_arguments)
        
    field_mappings = {}

    for required_field in required_fields:
        # Find the best match for each required field in dataset headers
        results = ranked_header_maps[required_field]
        print('-----------------------------------------')
        print(f'Target field: {required_field}')
        print('Potential matches found:')
        print('ID   Confidence\tField Name')
        print('-----------------------------------------')
        for i, aresult in enumerate(results):
            print('{:<2}   {:.2f}\t{:<10}'.format(i+1,aresult[1],aresult[0]))
        print('-----------------------------------------')
        print('Enter the ID of the field which most closely matches the target field.')
        print('If none of the options are a sutiable match, enter 0.')
        print('Enter \'x\' to stop.')
        user_input = input(f"Field ID: ").strip().lower()
        if user_input=='x':
            print('Stopping completeness check')
            break
        if user_input.isdigit():
            if int(user_input)>0 and int(user_input)<=5:
                os.system('cls' if os.name == 'nt' else 'clear')
                print(f'Chosen field: {results[int(user_input)-1][0]}')
                field_mappings[required_field] = results[int(user_input)-1][0]
            else:
                os.system('cls' if os.name == 'nt' else 'clear')
                print(f'Skipping field: {required_field}')
        else:
            os.system('cls' if os.name == 'nt' else 'clear')
            print(f'Input not recognized - skipping field: {required_field}')

    return field_mappings
