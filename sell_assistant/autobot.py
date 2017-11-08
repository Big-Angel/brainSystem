# -*- coding:utf-8 -*-
import os
import zipfile

from bot import Bot
from flask import Flask, request
from flask_cors import CORS
import _thread

app = Flask(__name__)
CORS(app)

bots = {}
bots_factor = {}
cfgs = '../cfgs/'

# TODO 加载所有话术内容，key-value: '话术编号':'话术bot'
for filename in os.listdir('../cfgs/'):
    bots_factor[filename] = Bot('../cfgs/' + filename)


@app.route("/version")
def version():
    return "v1.0.4"


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
        print("level:" + bots[session].get_label())
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


@app.route("/update", methods=['POST'])
def update():
    zip_file = request.files["file"]
    fname1 = ''
    if zip_file.filename.split('.')[1] == 'zip':
        zfile = zipfile.ZipFile(zip_file, 'r')
        finame = zfile.namelist()[0]
        if zip_file.filename.split('.')[0] != finame.split('/')[0]:
            finame = finame.encode("cp437").decode("utf-8")

        for fname in zfile.namelist():
            if zip_file.filename.split('.')[0] != fname.split('/')[0]:
                fname1 = fname.encode("cp437").decode("utf-8")
            else:
                fname1 = fname
            if fname1.find('__MACOSX') < 0:
                pathname = os.path.dirname(cfgs + fname1)
                if not os.path.exists(pathname) and pathname != "":
                    os.makedirs(pathname)
                data = zfile.read(fname)
                if not os.path.exists(cfgs + fname1):
                    fo = open(fname1, "wb")
                    fo.write(data)
                    fo.close
        zfile.close()
        if os.path.exists(cfgs + finame):
            _thread.start_new(updatebot, finame)
        return "successful"
    else:
        return 'not zip'


def updatebot(finame):
    bots_factor[finame] = Bot(cfgs + finame)


if __name__ == '__main__':
    app.run('0.0.0.0', 5000)
