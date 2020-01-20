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
        return wikipedia.suggest(ing)
    except:
        return ''


def get_wiki_summary(wiki_ing):
    try:
        return wikipedia.summary(wiki_ing)
    except:
        return ''


def get_wiki_production(wiki_ing):
    wp = wikipedia.page(wiki_ing)
    try:
        return wp.section('Production')
    except:
        return ''


def get_wiki_phrase(ing: str):
    '''Get the wikipedia string that concats the summary and if it exists, Production sections'''
    wiki_ing = get_wiki_suggested_ing(ing)
    wiki_phrase = get_wiki_summary(wiki_ing) + ' ' + get_wiki_production(wiki_ing)

    if wiki_phrase == ' ':
        print(f'WARNING: {ing} has no summary or production sections, or was not detected in wikipedia!')

    return wiki_phrase


def phrase_to_docvec(phrase: str, doc_embedding):
    phrase_s = Sentence(phrase.lower(), use_tokenizer=True)  # need to lower, since we're using the uncased version
    doc_embedding.embed(phrase_s)
    phrase_emb_tensor = phrase_s.get_embedding()  # get_embedding() returns a torch.FloatTensor

    return np.array(phrase_emb_tensor.data)


def add_to_embedding_dict(ing_name: str, ings_dict: Dict, source: str, doc_vector: np.array):
    if source=='wiki':
        ings_dict[ing_name]['vector']['wiki'] = doc_vector
    if source=='ewg':
        ings_dict[ing_name]['vector']['ewg'] = doc_vector

    pickle.dump(ings_dict, open('/Volumes/ja2/vegan/vegan_parser/data_source/ingredient_dictionary.p', 'wb'))

    return ings_dict



def text_only(image_text_string, ings_dict):

    # # define ingredient embedddings file
    # ings_dict_fp = '/Volumes/ja2/vegan/vegan_parser/data_source/ingredient_dictionary.p'
    #
    # try:
    #     ings_dict = pickle.load(open(ings_dict_fp, "rb"))
    # except FileNotFoundError:
    #     "Ingredients data not found!"

    cleaned_ings_list = create_ingredients_list(image_text_string)
    print(f'cleaned_ings_list: {cleaned_ings_list}')

    # Look up the data and pull out the relevant ingredients.
    # how should that be stored... list of dictionaries?

    ings_dict_list = []

    for ing in cleaned_ings_list:

        # look up ing in the dict
        ing_entry: Dict = ings_dict.get(ing)

        # if entry exists
        if ing_entry:
            # check if word vectors exist & create if needed, or just get them

            if ings_dict[ing].get('vectors'):

                if not ings_dict[ing]['vectors'].get(['ewg']):
                    # use the chemical_about phrase to create a document vector
                    phrase = ings_dict[ing].get(['chemical_about'])
                    if phrase:
                        ewg_docvec = phrase_to_docvec(phrase)
                    else:
                        ewg_docvec = None

                    ings_dict = add_to_embedding_dict(ing, ings_dict, 'ewg', ewg_docvec)
                    ings_dict[ing]['vectors']['ewg'] = ewg_docvec
                else:
                    # get the document vector if exists
                    ewg_docvec: Union[None, np.array] = ings_dict[ing]['vectors'].get(['ewg'])

                ing_entry['vectors']['ewg'] = ewg_docvec

                if not ings_dict[ing]['vectors'].get(['wiki']):
                    # use the wikipedia entry to create a document vector
                    phrase = get_wiki_phrase(ing)
                    if phrase:
                        wiki_docvec = phrase_to_docvec(phrase)
                    else:
                        wiki_docvec = None
                    ings_dict = add_to_embedding_dict(ing, ings_dict, 'wiki', wiki_docvec)
                    ings_dict[ing]['vectors']['wiki'] = wiki_docvec
                else:
                    wiki_docvec: Union[None, np.array] = ings_dict[ing]['vectors'].get(['wiki'])

                ing_entry['vectors']['wiki'] = wiki_docvec

            ings_dict_list.append(ing_entry)

        # entry does not exist in dict for whatever reason
        else:
            ings_dict_list.append('DID NOT FIND')

    # ings_dict_list is ready, now need to combine the data...somehow
    print(f'ings_dict_list: {ings_dict_list}')

    return cleaned_ings_list, ings_dict_list


def main(fp):

    # define ingredient embedddings file
    ings_dict_fp = '/Volumes/ja2/vegan/vegan_parser/data_source/ingredient_dictionary.p'

    try:
        ings_dict = pickle.load(open(ings_dict_fp, "rb"))
    except FileNotFoundError:
        "Ingredients data not found!"

    # image to text
    image_text_string = read_image(fp)
    cleaned_ings_list = create_ingredients_list(image_text_string)

    # Look up the data and pull out the relevant ingredients.
    # how should that be stored... list of dictionaries?

    ings_dict_list = []

    for ing in cleaned_ings_list:

        # look up ing in the dict
        ing_entry: Dict = ings_dict.get(ing)

        # if entry exists
        if ing_entry:
            # check if word vectors exist & create if needed, or just get them

            if ings_dict[ing].get('vectors'):

                if not ings_dict[ing]['vectors'].get(['ewg']):
                    # use the chemical_about phrase to create a document vector
                    phrase = ings_dict[ing].get(['chemical_about'])
                    if phrase:
                        ewg_docvec = phrase_to_docvec(phrase)
                    else:
                        ewg_docvec = None

                    ings_dict = add_to_embedding_dict(ing, ings_dict, 'ewg', ewg_docvec)
                    ings_dict[ing]['vectors']['ewg'] = ewg_docvec
                else:
                    # get the document vector if exists
                    ewg_docvec: Union[None, np.array] = ings_dict[ing]['vectors'].get(['ewg'])

                ing_entry['vectors']['ewg'] = ewg_docvec

                if not ings_dict[ing]['vectors'].get(['wiki']):
                    # use the wikipedia entry to create a document vector
                    phrase = get_wiki_phrase(ing)
                    if phrase:
                        wiki_docvec = phrase_to_docvec(phrase)
                    else:
                        wiki_docvec = None
                    ings_dict = add_to_embedding_dict(ing, ings_dict, 'wiki', wiki_docvec)
                    ings_dict[ing]['vectors']['wiki'] = wiki_docvec
                else:
                    wiki_docvec: Union[None, np.array] = ings_dict[ing]['vectors'].get(['wiki'])

                ing_entry['vectors']['wiki'] = wiki_docvec

            ings_dict_list.append(ing_entry)

        # entry does not exist in dict for whatever reason
        else:
            ings_dict_list.append('DID NOT FIND')

    # ings_dict_list is ready, now need to combine the data...somehow
    print(ings_dict_list)