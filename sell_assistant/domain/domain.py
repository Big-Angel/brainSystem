import os
from copy import copy

from utils.io import load_json
from sentence.sentence import Sentence
from attr_classifier.keyword import KeywordClassifier


class Domain:
    def __init__(self, path, global_hook=None):
        self.domain_cfg_path = path
        self.domain_name = self._get_domain_name()
        self.sentences = self._init_sentences(global_hook)
        self.clf = KeywordClassifier()

    def _init_sentences(self, global_hook=None):
        sentences = {}
        sentences_cfg = load_json(self.domain_cfg_path)
        for cfg in sentences_cfg.items():
            s_id = cfg[0]
            sentences[s_id] = Sentence(self.domain_name, cfg, global_hook)
        return sentences

    def _get_domain_name(self):
        return os.path.split(self.domain_cfg_path)[-1].split('.')[0]

    def say(self, sentence_id):
        return self.sentences[sentence_id].say()

    def answer(self, sentence_id, user_sentence, global_hook={}):
        sentence_idx = self.sentences[sentence_id].answer(user_sentence, global_hook)
        if ':' not in sentence_idx and sentence_idx != '恢复':
            return "%s:%s" % (self.domain_name, sentence_idx)
        else:
            return sentence_idx

    def get_sentence_idx(self, sentence_id, branch):
        return self.sentences[sentence_id].get_branch(branch)
