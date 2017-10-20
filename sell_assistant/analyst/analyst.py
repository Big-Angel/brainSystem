import os
import collections
from utils.io import load_json


class Analyst:
    def __init__(self, cfg_path):
        self.stat_cfg_path = os.path.join(cfg_path, 'stat')
        self.cfgs = self.parse_cfg()

    def parse_cfg(self):
        return collections.OrderedDict(load_json(os.path.join(self.stat_cfg_path, 'stat.json')))

    def analyze(self, conversations):
        def check_number(r):
            return int(r[0]) <= (len(conversations) - 1) < int(r[1])

        def check_keywords(keywords):
            for conversation in conversations:
                if len(conversation) > 1:
                    user_sentence = conversation[0]
                    for keyword in keywords:
                        if keyword in user_sentence:
                            return True
            return False

        support_ops = {
            'number': check_number,
            'keywords': check_keywords
        }
        default_res = 'E'
        res = 'E'
        for rule_number, cfg in self.cfgs.items():
            for op, rule in cfg['rule'].items():
                if op in support_ops:
                    if support_ops[op](rule):
                        res = cfg['label']
                        break
            if res != default_res:
                break
        return res
