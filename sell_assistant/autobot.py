from bot import Bot
from flask import Flask, request

app = Flask(__name__)
bot = Bot('../cfgs/huarui')


@app.route("/goon")
def reply():
    user_input = request.args.get("user_word")
    state, sentence = bot.answer(user_input)

    return str({
        "state": state,
        'sentence': sentence
    })


@app.route("/start")
def start():
    global bot
    bot = bot.reset()
    state, sentence = bot.start()

    return str({
        "state": state,
        'sentence': sentence
    })


if __name__ == '__main__':
    app.run('0.0.0.0', 5000)
