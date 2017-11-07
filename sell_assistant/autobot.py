# -*- coding:utf-8 -*-
import os
import zipfile


from bot import Bot
from flask import Flask, request

app = Flask(__name__)
bots = {}
bots_factor = {}
cfgs = '../cfgs/'

# TODO 加载所有话术内容，key-value: '话术编号':'话术bot'
for filename in os.listdir(cfgs):
    bots_factor[filename] = Bot(cfgs + filename)


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


@app.route("/update", methods=['POST'])
def update():
    zip_file = request.files["file"]
    fname1 = ''
    if zip_file.filename.split('.')[1] == 'zip':
        zfile = zipfile.ZipFile(zip_file, 'r')
        finame = zfile.namelist()[0]
        if zip_file.filename.split('.')[0] != finame.split('/')[0]:
            finame= finame.encode("cp437").decode("utf-8")

        for fname in zfile.namelist():
            if zip_file.filename.split('.')[0] != fname.split('/')[0]:
                fname1 = fname.encode("cp437").decode("utf-8")
            else:
                fname1 = fname
            if fname1.find('__MACOSX') < 0:
                pathname = os.path.dirname(cfgs+fname1)
                if not os.path.exists(pathname) and pathname != "":
                    os.makedirs(pathname)
                data = zfile.read(fname)
                if not os.path.exists(cfgs+fname1):
                    fo = open(fname1, "wb")
                    fo.write(data)
                    fo.close
        zfile.close()
        if os.path.exists(cfgs+finame):
            bots_factor[finame] = Bot(cfgs + finame)
        return "successful"
    else:
        return 'not zip'


if __name__ == '__main__':
    app.run('0.0.0.0', 5000)
