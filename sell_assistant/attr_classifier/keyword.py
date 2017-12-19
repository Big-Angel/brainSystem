# coding=utf-8
import re
import jieba
from jieba.analyse.tfidf import TFIDF


class KeywordClassifier:
    def __init__(self):
        self.local_threshold = 0.8
        self.global_hook_threshold = 0.8
        self.tfidf = TFIDF()

    def attrs_match(self, attrs, user_sentence):
        max_score = -1
        """totally match"""
        # 先匹配samples，再匹配patterns（正则），最后匹配关键字
        for attr_name, attr_cfg in attrs.items():
            samples = attr_cfg.get('samples', [])
            if isinstance(samples, str):
                samples = samples.split(' ')
            score = self.totally_match_score(user_sentence, samples)
            if score > max_score:
                max_score = score
                result = attr_name
        if max_score == 1.0:
            return max_score, result
        """regular expression match"""
        max_score = -1
        for attr_name, attr_cfg in attrs.items():
            patterns = attr_cfg.get('patterns', [])
            score = self.pattern_match_score(user_sentence, patterns)
            if score > max_score:
                max_score = score
                result = attr_name
        if max_score == 1.0:
            return max_score, result
        """keywords match"""
        max_score = (1, 0)
        words = list(jieba.cut(user_sentence, HMM=False))
        for attr_name, attr_cfg in attrs.items():
            keywords = attr_cfg.get('keywords', [])
            if isinstance(keywords, str):
                keywords = keywords.split(' ')
            score = self.keywords_match_score(words, keywords)
            if score > max_score:
                max_score = score
                result = attr_name
        if max_score != (1, 0):
            return 1.0, result

        return -1, None

    def predict(self, attrs, user_sentence, global_hook={}, allow_empty=False, default='pos'):
        """allow_empty for global qa"""
        """local attrs match"""
        max_score, result = self.attrs_match(attrs, user_sentence)
        if max_score >= self.local_threshold:
            return result
        """global hook match"""
        max_score, result = self.attrs_match(global_hook, user_sentence)
        if max_score >= self.global_hook_threshold:
            return result

        if allow_empty and max_score <= 0.0:
            return None
        else:
            return default

    def totally_match_score(self, user_sentence, samples):
        """totally match return 1.0"""
        for sample in samples:
            if sample == user_sentence:
                return 1.0
        return 0.0

    def pattern_match_score(self, user_sentence, patterns):
        for pattern in patterns:
            pattern = re.compile(pattern)
            if pattern.fullmatch(user_sentence):
                return 1.0
        return 0.0

    def keywords_match_score(self, user_words, keywords):
        max_score = (1, 0)
        for or_keyword in keywords:
            and_keywords = or_keyword.split(',')
            match_keywords = set(user_words).intersection(and_keywords)
            idf_score = 0
            for match_keyword in match_keywords:
                idf_score += self.tfidf.idf_freq.get(match_keyword, self.tfidf.median_idf)
            score = (len(match_keywords), idf_score)
            if score > max_score and len(match_keywords) == len(and_keywords):
                max_score = score
        return max_score


if __name__ == '__main__':
    clf = KeywordClassifier()

    attrs = {
        "pos": {
            "target": "了解情况:1",
            "keywords": ["嗯", "可以", "好的"]
        },
        "neg": {
            "target": "挽回:1",
            "keywords": ["不需要", "不用了", "没有", "物业费,价格"],
            "patterns": ["不.*要"]

        },
        "spe": {
            "target": "挽回:2",
            "keywords": ["你是谁", "干什么", "楼盘,价格"]
        }
    }

    jieba.add_word("你是谁")
    print(clf.predict(attrs, '干什么'))
    print(clf.predict(attrs, '物业费价格'))
