import os

from bot import Bot
from flask import Flask, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

bots = {}
bots_factor = {}

# TODO 加载所有话术内容，key-value: '话术编号':'话术bot'
for filename in os.listdir('../cfgs/'):
    bots_factor[filename] = Bot('../cfgs/' + filename)


@app.route("/version")
def version():
    return "v1.0.3"


@app.route("/goon")
def reply():
    user_input = request.args.get("user_word")
    session = request.args.get("session")

    if session is None:
        return str({
            "state": "error",
            "sentence": "[session] not exist, please check it on"
        })

    if session not in bots.keys():
        return str({
            "state": "结束",
            "sentence": "抱歉啦，我现在只能回复到这里了，请重新再来吧。"
        })

    state, sentence = bots[session].answer(user_input)

    if '结束' in state:
        bots.pop(session)

    return str({
        "state": state,
        'sentence': sentence
    })


@app.route("/start")
def start():
    # todo 添加话术参数，为后来的多种话术进行铺垫
    trick = request.args.get("trick")
    if trick is None:
        return str({
            "state": "error",
            "sentence": "parameter [trick] not exist."
        })
    bot_tmp = bots_factor[trick]
    if bot_tmp is None:
        return str({
            "state": "error",
            "sentence": "[trick] not record yet"
        })

    bot = bot_tmp.reset()

    session = request.args.get("session")
    if session is None:
        return str({
            "state": "error",
            "sentence": "[session] not exist, please check it on"
        })

    bots[session] = bot

    state, sentence = bot.start()

    return str({
        "state": state,
        'sentence': sentence
    })


if __name__ == '__main__':
    app.run('0.0.0.0', 5000)
