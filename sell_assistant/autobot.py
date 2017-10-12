import os

from bot import Bot
from flask import Flask, request

app = Flask(__name__)
bots = {}
bots_factor = {}

# TODO 加载所有话术内容，key-value: '话术编号':'话术bot'
for filename in os.listdir('../cfgs/'):
    bots_factor[filename] = Bot('../cfgs/'+filename)


@app.route("/goon")
def reply():
    user_input = request.args.get("user_word")
    session = request.args.get("session")

    if session is None:
        return "authority deny"

    if bots[session] is None:
        return "session not exist"

    state, sentence = bots[session].answer(user_input)

    if '结束' in state:
        bots.pop(session)

    return str({
        "state": state,
        'sentence': sentence
    })


@app.route("/start")
def start():
    global bot1
    bot = ''
    # todo 添加话术参数，为后来的多种话术进行铺垫
    trick = request.args.get("trick")
    bot = bots_factor[trick].reset()

    session = request.args.get("session")
    if session is None:
        return "authority deny"

    bots[session] = bot

    state, sentence = bot.start()

    return str({
        "state": state,
        'sentence': sentence
    })


if __name__ == '__main__':
    app.run('0.0.0.0', 5000)
