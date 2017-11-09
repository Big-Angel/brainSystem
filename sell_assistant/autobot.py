# -*- coding:utf-8 -*-
import csv
import json
import os
import zipfile
import datetime
from flask import Response

from bot import Bot
from flask import Flask, request
from flask_cors import CORS
from utils.hashcode import get_hash_code
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


@app.route("/update", methods=['POST'])
def update():
    zip_file = request.files["file"]
    if zip_file.filename.split('.')[1] == 'zip':
        zfile = zipfile.ZipFile(zip_file, 'r')
        finame = zfile.namelist()[0].split('/')[0].encode("cp437").decode("utf-8")
        for fname in zfile.namelist():
            if fname.find('.DS_Store') < 0 and fname.find('__MACOSX') < 0:
                fname1 = fname.encode("cp437").decode("utf-8")
                if fname.endswith('/'):
                    pathname = os.path.dirname(cfgs + fname1)
                    if not os.path.exists(pathname) and pathname != "":
                        os.makedirs(pathname)
                else:
                    data = zfile.read(fname)
                    fo = open(cfgs + fname1, "wb")
                    fo.write(data)
                    fo.close()
        zfile.close()
        if os.path.exists(cfgs + finame):
            try:
                _thread.start_new(update_bot, (finame,))
            except Exception as e:
                print(e)
        return str({'state': "successful",
                    'sentence': "上传成功"})

    else:
        return str({'state': 'error',
                    'sentence': 'not zip'})


def update_bot(finame):
    bots_factor[finame] = Bot(cfgs + finame)
    print("complete")


@app.route("/getDialogRecord")
def check_dialog_record():
    response = Response()
    trick = request.args.get("trick")
    if trick is None:
        return str({
            "state": "error",
            "sentence": "parameter [trick] not exist."
        })
    file_names = os.listdir(cfgs)
    if trick not in file_names:
        return str({
            "state": "error",
            "sentence": "not exist [trick]."
        })
    else:
        domain_file = os.listdir(cfgs + '/' + trick + '/domain/')
        domain_file_info = {}
        writer = csv.writer(response.stream)
        fileHeader = ['场景', '话术文本', '录音名']
        writer.writerow(fileHeader)
        for file in domain_file:
            with open(cfgs + '/' + trick + '/domain/' + file) as json_file:
                data = json.load(json_file)
                for k, v in data.items():
                    stage = (file.split('.')[0] + '' + k)
                    sentence = v['sentence']
                    name = trick + get_hash_code(sentence) + '.pcm'
                    domain_file_info.update({stage: sentence})
                    writer.writerow([stage, sentence, name])
            json_file.close()
        with open(cfgs + '/' + trick + '/qa/qa.json') as qa:
            data = json.load(qa)
            for k, v in data.items():
                stage1 = 'qa' + k
                sentence1 = v['sentence']
                for k, v in domain_file_info.items():
                    stage = stage1 + k
                    sentence = sentence1 + v
                    name = trick + get_hash_code(sentence) + '.pcm'
                    writer.writerow([stage, sentence, name])
        qa.close()
    response.mimetype = 'text/csv'
    response.charset = 'gbk'
    response.headers = {'Content-disposition': 'attachment; filename=' + trick +
                                               datetime.datetime.today().strftime('%Y%m%d') + '.csv;'}
    return response


if __name__ == '__main__':
    app.run('0.0.0.0', 5000)
