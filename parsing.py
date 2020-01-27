"""Collection of functions to parse ingredients labels.
 From Image -> Strings -> Embeddings & lookup.
 In progress."""
import os
import sys
import pickle
from string import punctuation
import re
from PIL import Image
import pytesseract
from typing import List, Dict, Union
import numpy as np
from scipy.spatial.distance import cosine as cosine_distance

import wikipedia
from flair.data import Sentence
from flair.embeddings import BertEmbeddings
from flair.embeddings import DocumentPoolEmbeddings

# load embedding frameworks
bert_embedding = BertEmbeddings("bert-base-uncased")  # takes a long time to import!
doc_embedding = DocumentPoolEmbeddings([bert_embedding], fine_tune_mode='nonlinear')



def read_image(filepath: str) -> str:
    """
    :param fp: filepath of image
    :return: string from ingredient label

    """
    # TODO: add image editing to create better image before outputting the string.

    return str(((pytesseract.image_to_string(Image.open(filepath)))))


def create_ingredients_list(text: str) -> List[str]:
    """
    :param text: The output from read_image: a single string of instruments.
    :return: a list of strings of ingredients
    """

    text = re.sub("\s+", ' ', text)  # change any non-single spaces to single spaces
    lower_text = text.lower()

    # strip out the "ingredients:" section
    lower_text_stripped = re.sub('ingredients\S+|ingredients', '', lower_text)

    # TODO: deal with 1) what if it's split on non-commas? 2) what about wrapped words?
    #  e.g. extr-act -> extract, vs dash that is supposed to be there.
    #  Not to mention other problems with text detection...

    # what might the commas be ingredients be interpreted as?
    lower_text_stripped = re.split('[.,;]', lower_text_stripped)

    cleaned_ings = clean_ingredients_list(lower_text_stripped)
    return cleaned_ings


def clean_ingredients_list(ings: List[str]) -> List[str]:
    '''
    :param ings: list of lowercased ingredient strings
    :return: list of cleaned ingredients
    '''
    clean_ings = []

    # let's ignore water. There is likely a better way to do this.
    water_list = ['water', 'aqua', 'deionized water', 'distilled water', 'onsen-sui',
                  'purified water', 'water/aqua']

    for ing in ings:
        clean_ing = clean_ingredient_string(ing)
        if clean_ing not in water_list:
            clean_ings.append(clean_ing)

    return clean_ings


def clean_ingredient_string(ing: str) -> str:
    return ing.strip()


def get_wiki_suggested_ing(ing: str) -> str:
    ing = ing.lower()
    try:
        print(wikipedia.search(ing))
        return wikipedia.search(ing)[0]
        # return wikipedia.suggest(ing)  # this is not returning all options
    except:
        return ''


def get_wiki_summary(wiki_ing):
    if wikipedia.summary(wiki_ing) is not None:
        return wikipedia.summary(wiki_ing)
    else:
        return ''


def get_wiki_production(wiki_ing):
    wp = wikipedia.page(wiki_ing)
    if wp.section('Production') is not None:
        return wp.section('Production')
    else:
        return ''


def get_wiki_phrase(ing: str) -> Union[str, None]:
    '''Get the wikipedia string that concats the summary and if it exists, Production sections'''

    try:
        wiki_ing = get_wiki_suggested_ing(ing)
        wiki_phrase = get_wiki_summary(wiki_ing) + ' ' + get_wiki_production(wiki_ing)
        wiki_phrase = wiki_phrase[:2000]  # because the document vector model can only handle up to ~2000 chars

        if wiki_phrase == ' ':
            print(f'WARNING: {ing} has no summary or production sections, or was not detected in wikipedia!')
            wiki_phrase = None

    except:
        print(f'WARNING: {ing} does not return a valid wiki page! Setting to None.')
        wiki_phrase = None

    return wiki_phrase


def phrase_to_docvec(phrase: str, doc_embedding=doc_embedding):

    # need to crop the phrase to the first 2000 characters unless I want to look up more things. Should be good enough.
    phrase_s = Sentence(phrase[:2000].lower(), use_tokenizer=True)  # need to lower, since we're using the uncased version
    doc_embedding.embed(phrase_s)
    phrase_emb_tensor = phrase_s.get_embedding()  # get_embedding() returns a torch.FloatTensor

    return np.array(phrase_emb_tensor.data)


def add_to_embedding_dict(ing_name: str, ings_dict: Dict, source: str, doc_vector: np.array):
    if source=='wiki':
        ings_dict[ing_name].update({'wiki_vector': doc_vector})
    if source=='ewg':
        ings_dict[ing_name].update({'ewg_vector': doc_vector})

    pickle.dump(ings_dict, open('/Volumes/ja2/vegan/vegan_parser/data_source/ingredient_dictionary.p', 'wb'))

    return ings_dict



def text_only_main(image_text_string, ings_dict, definitions_dict):

    # # define ingredient embedddings file
    # ings_dict_fp = '/Volumes/ja2/vegan/vegan_parser/data_source/ingredient_dictionary.p'
    #
    # try:
    #     ings_dict = pickle.load(open(ings_dict_fp, "rb"))
    # except FileNotFoundError:
    #     "Ingredients data not found!"

    cleaned_ings_list = create_ingredients_list(image_text_string)
    print(f'cleaned_ings_list: {cleaned_ings_list}')
    print()

    # Look up the data and pull out the relevant ingredients.
    # how should that be stored... list of dictionaries?

    ings_dict_list = []

    for ing in cleaned_ings_list:
        print(f'Working on ingredient: {ing}')

        # look up ing in the dict
        ing_entry: Dict = ings_dict.get(ing)


        # if entry exists
        if ing_entry:

            # check if word vectors exist & create if needed, or just get them

            # print(ing_entry)

            if ings_dict[ing].get('ewg_vector') is None:
                try:
                    # use the chemical_about phrase to create a document vector
                    phrase = ings_dict[ing].get('chemical_about')
                    if phrase:
                        ewg_docvec = phrase_to_docvec(phrase, doc_embedding)
                    else:
                        ewg_docvec = None

                    ings_dict = add_to_embedding_dict(ing, ings_dict, 'ewg', ewg_docvec)
                    ings_dict[ing]['ewg_vector'] = ewg_docvec
                except:
                    ewg_docvec = None
            else:
                # get the document vector if exists
                ewg_docvec: Union[None, np.array] = ings_dict[ing].get('ewg_vector')

            ing_entry['ewg_vector'] = ewg_docvec

            if ings_dict[ing].get('wiki_vector') is None:
                # ing is in dict but does not have wiki_vector
                try:
                    # use the wikipedia entry to create a document vector
                    phrase = get_wiki_phrase(ing)
                    if phrase:
                        wiki_docvec = phrase_to_docvec(phrase, doc_embedding)
                    else:
                        wiki_docvec = None
                except:
                    wiki_docvec = None

                ings_dict = add_to_embedding_dict(ing, ings_dict, 'wiki', wiki_docvec)
                ings_dict[ing]['wiki_vector'] = wiki_docvec

            else:
                # wiki_vector exists
                wiki_docvec: Union[None, np.array] = ings_dict.get('wiki_vector')

            ing_entry['wiki_vector'] = wiki_docvec

            # Now compare the ingredient against the vectors and find closest definition
            if (ing_entry.get('wiki_vector') is None) and (ing_entry.get('ewg_vector') is not None):
                vector = ing_entry.get('ewg_vector')
            elif (ing_entry.get('wiki_vector') is not None) and (ing_entry.get('ewg_vector') is None):
                vector = ing_entry.get('wiki_vector')
            elif (ing_entry.get('wiki_vector') is not None) and (ing_entry.get('ewg_vector') is not None):
                vector = np.mean([ing_entry.get('wiki_vector'), ing_entry.get('ewg_vector')], axis=0)
            else:
                vector = None

            # Then take the cosine_similarity with all 4 reference vectors to get class

            prev_min_key = None
            prev_min_distance = None

            for key in definitions_dict.keys():
                print(key)
                print(cosine_distance(definitions_dict[key], vector))

                if prev_min_key is None:
                    prev_min_key = key
                    min_key = key
                    prev_min_distance = cosine_distance(definitions_dict[key], vector)

                else:
                    if cosine_distance(definitions_dict[key], vector) < prev_min_distance:
                        min_key = key
                        min_dist = cosine_distance(definitions_dict[key], vector)
                        prev_min_distance = min_dist
                        # prev_min_key = key

            # And add the type to the ingredient
            ing_entry['type'] = min_key.split('_')[0]  # because of the way I designed the names of the dictionary

            # add to entry for this ing
            ings_dict_list.append(ing_entry)

        # entry does not exist in dict for whatever reason
        else:
            # ings_dict_list.append('DID NOT FIND')
            ings_dict_list.append(None)

    # ings_dict_list is ready, now need to combine the data...somehow
    # print(f'ings_dict_list: {ings_dict_list}')


    return cleaned_ings_list, ings_dict_list


def compile_detected_results(cleaned_ings_list, ings_dict_list):
    """

    :param cleaned_ings_list: list of the detected ingredients.
    :param ings_dict_list:
    :return:
    """

    # Now let's compile the results.
    print()
    print("---Compiled Results----")

    entries_in_db = []
    all_entries_with_status = []
    for entry, ing_name in zip(ings_dict_list, cleaned_ings_list):
        if entry is not None:
            entries_in_db.append(entry)
            all_entries_with_status.append(ing_name + f" - estimated {entry['type']}")
        else:
            all_entries_with_status.append(ing_name + ' - not found in database!')


    print(f"Info found for {len(entries_in_db)} of {len(ings_dict_list)} detected ingredients.")

    ings_detected_str = "\n\t".join(all_entries_with_status)
    print(f'Ingredients detected:')
    print(f'\t{ings_detected_str}')

    print()

    # Create fractions for weighting, using a simple linear relationship between detected ingredients
    raw_counts = [len(entries_in_db) - i for i, ing in enumerate(entries_in_db)]
    ing_fractions = np.array(raw_counts) / sum(raw_counts)

    # Calculate fractions from each substance contributing to the final item. Should sum to ~1.
    substance_weights = list(zip(ing_fractions, [d['type'] for d in entries_in_db]))

    mi = 0
    pl = 0
    pe = 0
    an = 0
    for item in substance_weights:
        if item[1].startswith('mi'):
            mi+=item[0]
        elif item[1].startswith('pl'):
            pl+=item[0]
        elif item[1].startswith('pe'):
            pe+=item[0]
        else:
            an+=item[0]

    # Fractions making up the subtance
    print("Estimated composition:")
    print(f'\tmineral: {round(100*mi, 1)}%, plant: {round(100*pl, 1)}%, petroleum: {round(100*pe, 1)}%, animal: {round(100*an, 1)}%')

    # And the safety score
    score = 0
    for elem in zip([d['mean_score'] for d in entries_in_db], ing_fractions):
        score += elem[0]*elem[1]

    print("Estimated Safety Score:")
    print(f'\t{round(score, 1)}')



#
# def main(fp):
#
#     # define ingredient embedddings file
#     ings_dict_fp = '/Volumes/ja2/vegan/vegan_parser/data_source/ingredient_dictionary.p'
#
#     try:
#         ings_dict = pickle.load(open(ings_dict_fp, "rb"))
#     except FileNotFoundError:
#         "Ingredients data not found!"
#
#     # image to text
#     image_text_string = read_image(fp)
#     cleaned_ings_list = create_ingredients_list(image_text_string)
#
#     # Look up the data and pull out the relevant ingredients.
#     # how should that be stored... list of dictionaries?
#
#     ings_dict_list = []
#
#     for ing in cleaned_ings_list:
#
#         # look up ing in the dict
#         ing_entry: Dict = ings_dict.get(ing)
#
#         # if entry exists
#         if ing_entry:
#             # check if word vectors exist & create if needed, or just get them
#
#             if ings_dict[ing].get('vectors'):
#
#                 if not ings_dict[ing]['vectors'].get(['ewg']):
#                     # use the chemical_about phrase to create a document vector
#                     phrase = ings_dict[ing].get(['chemical_about'])
#                     if phrase:
#                         ewg_docvec = phrase_to_docvec(phrase)
#                     else:
#                         ewg_docvec = None
#
#                     ings_dict = add_to_embedding_dict(ing, ings_dict, 'ewg', ewg_docvec)
#                     ings_dict[ing]['vectors']['ewg'] = ewg_docvec
#                 else:
#                     # get the document vector if exists
#                     ewg_docvec: Union[None, np.array] = ings_dict[ing]['vectors'].get(['ewg'])
#
#                 ing_entry['vectors']['ewg'] = ewg_docvec
#
#                 if not ings_dict[ing]['vectors'].get(['wiki']):
#                     # use the wikipedia entry to create a document vector
#                     phrase = get_wiki_phrase(ing)
#                     if phrase:
#                         wiki_docvec = phrase_to_docvec(phrase)
#                     else:
#                         wiki_docvec = None
#                     ings_dict = add_to_embedding_dict(ing, ings_dict, 'wiki', wiki_docvec)
#                     ings_dict[ing]['vectors']['wiki'] = wiki_docvec
#                 else:
#                     wiki_docvec: Union[None, np.array] = ings_dict[ing]['vectors'].get(['wiki'])
#
#                 ing_entry['vectors']['wiki'] = wiki_docvec
#
#             ings_dict_list.append(ing_entry)
#
#         # entry does not exist in dict for whatever reason
#         else:
#             ings_dict_list.append('DID NOT FIND')
#
#     # ings_dict_list is ready, now need to combine the data...somehow
#     print(ings_dict_list)