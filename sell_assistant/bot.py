import copy
import os
from graph.graph import Graph
from utils.io import load_json
from attr_classifier.keyword import KeywordClassifier


class Bot:
    def __init__(self, cfg_path):
        # constance.
        self.cfg_path = cfg_path
        self.init_sentence = "开场白:1"
        self.retrieve_sentence = "挽回:1"
        self.invite_sentence = "邀约:1"
        self.end_sentence = "结束:1"
        self.latest_response = ""
        self.global_events_cfg_path = os.path.join(self.cfg_path, 'global_events')

        # class instance.
        self.graph = Graph(self.cfg_path, self.init_sentence)
        self.global_events = self._init_global_events()

    def reset(self):
        return copy.deepcopy(self)

    def start(self):
        return self.answer(init=True)

    def answer(self, sentence=None, init=False):
        if not sentence and init:
            self.latest_response = self.graph.say(self.init_sentence)
            return self.latest_response
        else:
            """global event"""
            event = self.global_events.answer(sentence)
            if event:
                return self.global_events_action(event)
            else:
                """按照流程走"""
                self.latest_response = self.graph.answer(sentence)
                return self.latest_response

    def _init_global_events(self):
        return GlobalEvent(os.path.join(self.global_events_cfg_path, 'global.json'))

    def global_events_action(self, event):
        if event == "不清楚":
            return self.latest_response
        if event == "拒绝":
            return self.graph.say(self.retrieve_sentence)
        if event == "邀约":
            return self.graph.say(self.invite_sentence)
        if event == "结束":
            return self.graph.say(self.end_sentence)


class GlobalEvent:
    def __init__(self, cfg_path):
        self.cfg_path = cfg_path
        self.cfg = load_json(self.cfg_path)
        self.clf = KeywordClassifier()
        self.event_cnt = self._init_cnt()

    def __deepcopy__(self, memodict=None):
        ge = copy.copy(self)
        ge.event_cnt = self._init_cnt()  # cause even_cnt would be modified on the processing, so need to reset.
        return ge

    def answer(self, user_sentence):
        event = self.clf.predict(self.cfg, user_sentence, allow_empty=True)
        if event:
            self.event_cnt[event] += 1
            if self.event_cnt[event] <= self.cfg[event].get('limit', 999):
                return event
            else:
                return self.cfg[event].get('end')
        else:
            return None

    def _init_cnt(self):
        event_cnt = {}
        for event_name, event_cfg in self.cfg.items():
            event_cnt[event_name] = 0
        return event_cnt
