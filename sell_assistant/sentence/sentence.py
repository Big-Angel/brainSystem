import jieba
from attr_classifier.keyword import KeywordClassifier


class Sentence:
    def __init__(self, domain_name, cfg, global_hook=None):  # global_hook:全局关键词 cfg:json文件内容
        self.domain_name = domain_name  # e.g.: domain_name = "了解情况"
        self.id = cfg[0]  # e.g.: 1
        self.cfg = cfg[1]  # e.g.: {"sentence":..."next":..."default":...}
        self._init_sentence()
        self.clf = KeywordClassifier()
        self._init_global_hook(global_hook)
        self._init_jieba()

    def _init_sentence(self):
        self.sentence = self.cfg['sentence']
        self.next = self.cfg['next']

    def _init_global_hook(self, global_hook):
        for attr_name, attr_cfg in self.next.items():
            if attr_name not in ['pos', 'neg']:
                global_hook[self.domain_name + attr_name] = attr_cfg

    def _init_jieba(self):
        # 迭代，把当前domain中next下面的所有的关键字都加到jieba字典里
        for attr_name, attr_cfg in self.next.items():
            keywords = attr_cfg.get('keywords', [])  # 如果keyword不存在，则返回一个空列表
            if isinstance(keywords, str):
                keywords = keywords.split(' ')
            """["楼盘,价格", "价格"]"""
            for or_keyword in keywords:
                and_keywords = or_keyword.split(',')
                for keyword in and_keywords:
                    jieba.add_word(keyword)

    def say(self):
        # 返回json中的sentence
        return self.sentence

    def get_branch(self, branch):
        return self.next[branch]['target']

    def answer(self, user_sentence, global_hook={}):
        default = self.cfg.get('default', 'pos')
        branch = self.clf.predict(self.next, user_sentence, global_hook, default=default)
        if branch in self.next:
            return self.next[branch]['target']
        elif branch in global_hook:
            return global_hook[branch]['target']
