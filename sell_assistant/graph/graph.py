import os
from copy import copy

from domain.domain import Domain
from utils.io import load_json
from attr_classifier.keyword import KeywordClassifier


class QA:
    def __init__(self, cfg_path):
        self.cfg_path = cfg_path
        self.cfg = load_json(self.cfg_path)
        self.clf = KeywordClassifier()

    def answer(self, user_sentence):
        branch = self.clf.predict(self.cfg, user_sentence, allow_empty=True)
        if branch:
            return self.cfg[branch]['sentence']
        else:
            return None


class Graph:
    g_init_sentence = None

    def __init__(self, cfg_path, init_sentence="开场白:1"):
        self.graph_cfg_path = os.path.join(cfg_path, 'graph')
        self.domains_cfg_path = os.path.join(cfg_path, 'domain')
        self.qa_cfg_path = os.path.join(cfg_path, 'qa')
        self.flow = self._init_mainflow()
        self.global_hook = {}
        self.domains = self._init_domains()
        self.qa = self._init_qa()
        self.current_sentence = init_sentence
        self.saved_sentence_idx = init_sentence
        self.next_say = None  # 存储下一句话，不连续讲的需求
        Graph.g_init_sentence = init_sentence

    def __deepcopy__(self, memodict=None):
        gph = copy(self)
        gph.current_sentence = Graph.g_init_sentence
        gph.saved_sentence_idx = Graph.g_init_sentence

        return gph

    def _init_mainflow(self):
        """
        :return: A list, ['domain1', 'domain2'...]
        """
        return load_json(os.path.join(self.graph_cfg_path, 'graph.json')).get('flow')

    def _init_domains(self):
        domains = {}
        domain_cfgs = os.listdir(self.domains_cfg_path)
        for cfg in domain_cfgs:
            if cfg.endswith(".json"):
                domain_name = cfg[:-5]
                domains[domain_name] = Domain(os.path.join(self.domains_cfg_path, cfg), self.global_hook)
        return domains

    def _init_qa(self):
        return QA(os.path.join(self.qa_cfg_path, 'qa.json'))

    def answer(self, user_sentence):
        """global QA"""
        global_response = self.qa.answer(user_sentence)
        if not global_response and self.next_say:
            state, response = self.next_say
            self.next_say = None
            return state, response
        """domain回答的流程"""
        if global_response:
            """如果是全局回答，那么下一句话就是当前句子的pos分支"""
            state, graph_response = self.say(self._get_sentence_idx(self.current_sentence, 'pos'))
            self.next_say = (state, graph_response)
            sentence_idx = state
        else:
            domain_name, sentence_id = self.current_sentence.split(':')
            sentence_idx = self.domains[domain_name].answer(sentence_id, user_sentence, self.global_hook)

        if '挽回' not in sentence_idx and '恢复' not in sentence_idx:
            self.saved_sentence_idx = sentence_idx

        if '恢复' in sentence_idx:
            state, graph_response = self.say(self._get_sentence_idx(self.saved_sentence_idx, 'pos'))
            if global_response:
                self.next_say = state, graph_response
            return state, global_response if global_response else graph_response
        else:
            state, graph_response = self.say(sentence_idx)
            if global_response:
                self.next_say = state, graph_response
            return state, global_response if global_response else graph_response

    def say(self, sentence_idx):
        self.current_sentence = sentence_idx
        domain_name, sentence_id = sentence_idx.split(':')
        return self.current_sentence, self.domains[domain_name].say(sentence_id)

    def _get_sentence_idx(self, sentence_idx, branch):
        domain_name, sentence_id = sentence_idx.split(':')
        return self.domains[domain_name].get_sentence_idx(sentence_id, branch)
