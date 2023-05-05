import sys

import dill


class ReadBookOrNotClassifier:
    def __init__(self):
        import pickle
        self.pkl_loader = pickle.loads
        self.classes = ['да', 'нет']
        self.yes_lemms = ['да', 'слышать', 'знать', 'читать', 'ага', 'конечно']
        self.no_lemms = ['нет', 'не', 'ни', 'неа']

    def predict_proba(self, tokenized_elements_list_pkl):
        import numpy
        probability_answer = numpy.array([[0, 0]])
        list_of_tokens = self.pkl_loader(tokenized_elements_list_pkl)
        set_lemms = {token.get('lemma', '') for token in list_of_tokens}

        yes_intersection = set(self.yes_lemms) & set_lemms
        no_intersection = set(self.no_lemms) & set_lemms

        len_yes_intersection = len(yes_intersection)
        len_no_intersection = len(no_intersection)

        if len_yes_intersection > 0 and len_no_intersection == 0:
            probability_answer = numpy.array([[1, 0]])

        if len_no_intersection > 0:
            probability_answer = numpy.array([[0, 1]])

        return probability_answer


py_version = sys.version_info
py_suffix = f"_py{py_version.major}{py_version.minor}"

with open(f"ReadBookOrNotClassifier{py_suffix}.pkl", "wb+") as fd:
    dill.dump(ReadBookOrNotClassifier(), fd)
