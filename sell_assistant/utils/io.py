import json


def load_json(path):
    try:
        with open(path, encoding='utf-8') as f:
            cfg = json.load(f)
        return cfg
    except FileNotFoundError:
        print("%s not found" % path)
        exit(-1)
    except Exception as e:
        print(e)
        exit(-1)
