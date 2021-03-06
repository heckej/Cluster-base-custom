from fuzzywuzzy import fuzz
import gensim
import numpy as np
import pandas as pd
from nltk import word_tokenize
from nltk.corpus import stopwords
from scipy.spatial.distance import cosine, cityblock, jaccard, canberra, euclidean, minkowski, braycurtis
import xgboost as xgb
from sklearn.preprocessing import StandardScaler
import pickle

stop_words = set(stopwords.words("english"))

W2VModel = gensim.models.KeyedVectors.load_word2vec_format("GoogleNews-vectors-negative300-SLIM.bin.gz", binary=True)

# Load the question matching model with 4 threads
bst_loaded = xgb.Booster({"nthread": 4})
bst_loaded.load_model("0001.model")

feature_labels =\
    ['len_q1', 'len_q2', 'diff_len', 'len_char_q1', 'len_char_q2',
     'len_word_q1', 'len_word_q2', 'common_words', 'fuzz_QRatio',
     'fuzz_WRatio', 'fuzz_partial_ratio', 'fuzz_partial_token_set_ratio',
     'fuzz_partial_token_sort_ratio', 'fuzz_token_set_ratio', 'fuzz_token_sort_ratio',
     'cosine_distance', 'cityblock_distance', 'jaccard_distance', 'canberra_distance', 'euclidean_distance',
     'minkowski_distance', 'braycurtis_distance', 'wmd', 'norm_wmd']

# 1x uitvoeren
# nltk.download("punkt")
# nltk.download("stopwords")

"""
Method getFeatures(question1, question2) returns dictionary of features given two questions
"len_q1"                            =   length of the first string
"len_q2"                            =   length of second string
"diff_len"                          =   difference in length (len_q1-len_q2)
"len_char_q1"                       =   length of the first string without the spaces
"len_char_q2"                       =   length of the second string without the spaces
"len_word_q1"                       =   word count of the first string
"len_word_q2"                       =   word count of the second string
"common_words"                      =   count of words the two strings have in common
"fuzz_Qratio"                       =   Q ratio of the strings
"fuzz_Wratio"                       =   W ratio of the string
"fuzz_partial_ratio"                =   partial ratio of the strings
"fuzz_partial_token_set_ratio"      =   partial token set ratio
"fuzz_partial_token_sort_ratio"     =   partial token sort ratio
"fuzz_token_set_ratio"              =   token set ratio
"fuzz_token_sort_ratio"             =   token sort ratio
"cosine_distance": cosine(W2V[0], W2V[1]),
"cityblock_distance": cityblock(W2V[0], W2V[1]),
"jaccard_distance": jaccard(W2V[0], W2V[1]),
"canberra_distance": canberra(W2V[0], W2V[1]),
"euclidean_distance": euclidean(W2V[0], W2V[1]),
"minkowski_distance": minkowski(W2V[0], W2V[1]),
"braycurtis_distance": braycurtis(W2V[0], W2V[1]),
"wmd": W2V[2],
"norm_wmd": W2V[3]
"""


def get_features(question1, question2):
    """
    Get all the features to input into the XGBoost model.

    Pre: Both questions cannot be None.
    Args:
        question1: The first question to match.
        question2: The second question to match.

    Returns: A dictionary with all the features for the XGBoost model.

    """
    w2v = word2vec_features(question1, question2, W2VModel)
    output_dict = {
        # length based features
        "len_q1": [len(question1)],
        "len_q2": [len(question2)],
        "diff_len": [len(question1) - len(question2)],
        "len_char_q1": [len(question1.replace(" ", ""))],
        "len_char_q2": [len(question2.replace(" ", ""))],
        "len_word_q1": [len(question1.split())],
        "len_word_q2": [len(question2.split())],
        "common_words": [len(set(question1.lower().split()).intersection(set(question2.lower().split())))],
        # distance based features
        #   (fuzzywuzzy library tutorial: https://www.datacamp.com/community/tutorials/fuzzy-string-python)
        "fuzz_Qratio": [fuzz.QRatio(question1, question2)],
        "fuzz_Wratio": [fuzz.WRatio(question1, question2)],
        "fuzz_partial_ratio": [fuzz.partial_ratio(question1, question2)],
        "fuzz_partial_token_set_ratio": [fuzz.partial_token_set_ratio(question1, question2)],
        "fuzz_partial_token_sort_ratio": [fuzz.partial_token_sort_ratio(question1, question2)],
        "fuzz_token_set_ratio": [fuzz.token_set_ratio(question1, question2)],
        "fuzz_token_sort_ratio": [fuzz.token_sort_ratio(question1, question2)],

        # word2vec based features
        "cosine_distance": [cosine(w2v[0], w2v[1])],
        "cityblock_distance": [cityblock(w2v[0], w2v[1])],
        "jaccard_distance": [jaccard(w2v[0], w2v[1])],
        "canberra_distance": [canberra(w2v[0], w2v[1])],
        "euclidean_distance": [euclidean(w2v[0], w2v[1])],
        "minkowski_distance": [minkowski(w2v[0], w2v[1])],
        "braycurtis_distance": [braycurtis(w2v[0], w2v[1])],
        "wmd": [w2v[2]],
        "norm_wmd": [w2v[3]]

    }
    return output_dict


def match(question1, question2):
    """
    Compute and return the probability that the two given questions are semantically the same.

    Args:
        question1: The first question
        question2: The second question

    Returns: The probability that the two given questions are semantically the same as a float p (1 = equal, 0 = different, 0 <= p <= 1)

    """
    # Calculate the features
    features = get_features(question1, question2)
    # Transform the featuers to a pd DataFrame
    features = pd.DataFrame(features, columns=feature_labels)
    # Clean up infinites and NaNs
    features = features.replace([np.inf, -np.inf], np.nan).fillna(0).values
    # Load the scaler and scale the data
    scaler = pickle.load(open("scaler.p", "rb"))
    features = scaler.transform(features)
    # Give the features to the model for prediction
    model_input = xgb.DMatrix(features)
    pred = bst_loaded.predict(model_input)
    return pred[0]


def get_wmd(question1, question2, model):
    """
    Get the word-mover's distance between the two given questions.

    Pre: No parameters may be None.
    Args:
        question1: The first question to match.
        question2: The second question to match.
        model: A word2vec-model.

    Returns: The word-mover's distance between the two questions.

    """
    s1 = question1.lower().split()
    s2 = question2.lower().split()
    s1 = [w for w in s1 if w not in stop_words]
    s2 = [w for w in s2 if w not in stop_words]
    return model.wmdistance(s1, s2)


def word2vec_features(question1, question2, model):
    """
    Get the word2vec features of the two questions.

    Pre: No parameters may be None.
    Args:
        question1: The first question to match.
        question2: The second question to match.
        model: A word2vec-model.

    Returns: A list with the word2vec features between the two questions.

    """
    # Calculate the sent2vec vectors for every question
    w2v_q1 = np.array(sent2vec(question1, model))
    w2v_q2 = np.array(sent2vec(question2, model))
    wmd = get_wmd(question1, question2, model)
    model.init_sims(replace=True)
    norm_wmd = get_wmd(question1, question2, model)
    return [w2v_q1, w2v_q2, wmd, norm_wmd]


# Google's Word2vec model expects words as input, so sentences must be
# transformed to vectors indirectly
def sent2vec(s, model):
    """
    Transform a sentence to a vector.

    Pre: No parameters may be None.
    Args:
        s: The sentence to transform.
        model: A word2vec model.

    Returns: A vector, representing the given sentence.

    """
    words = word_tokenize(s.lower())
    # Stopwords and numbers must be removed, as well as words that are not
    # part of the model
    M = [model[w] for w in words if w not in stop_words and w.isalpha() and w in model]
    M = np.array(M)
    if len(M) > 0:
        v = M.sum(axis=0)
        return v / np.sqrt((v ** 2).sum())
    else:
        # When the sentence is empty after removing unvalid tokens, the vector
        # is equal to the null-vector
        return model.get_vector('null')


"""
prediction = match("Where is the coffee machine?", "Where can I find the coffee machine?")
print(prediction)
prediction = match("Where is the coffee machine?", "When did the Titanic sink?")
print(prediction)
prediction = match("How can I open the coffee machine?", "Where is the coffee machine?")
print(prediction)
prediction = match("How big is the coffee machine?", "How can I use the coffee machine?")
print(prediction)
prediction = match("Where is the coffee machine?", "Where is the coffee machine?")
print(prediction)
"""
