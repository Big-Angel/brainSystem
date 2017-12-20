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
import xlwt
import _thread
import requests
import hashlib

app = Flask(__name__)
CORS(app)

bots = {}
bots_factor = {}

# TODO 加载所有话术内容，key-value: '话术编号':'话术bot'
TRICKS_PATH = "../cfgs/tricks/"
AUTOSERVICE_HOST = "http://localhost:8082"
AUTOSERVISE_TRICK_UPDATE_URL = "/admin/sales-pitches/operate/update"
m = hashlib.md5()
m.update("12345678".encode("utf-8"))
TOKEN = m.hexdigest()

for filename in os.listdir(TRICKS_PATH):
    # 过滤隐藏文件
    if not filename.startswith("."):
        bots_factor[filename] = Bot(TRICKS_PATH + filename)


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
        rate = bots[session].get_label()
        print("level:" + rate)
        bots.pop(session)
        # 结束阶段返回对应的意向登记评分
        return str({
            "state": state,
            "sentence": sentence,
            "rate": rate,
        })

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
    if trick not in bots_factor:
        return str({
            "result": False,
            "data": "[trick] not exist."
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
    try:
        global AUTOSERVICE_HOST
        zip_file = request.files["file"]
        trick_name = request.form["trick"]
        trick_no = request.form["trickNo"]

        if "recall_addr" in request.form.keys():
            AUTOSERVICE_HOST = request.form["recall_addr"]

        if zip_file.filename.split('.')[1] == 'zip':
            zfile = zipfile.ZipFile(zip_file, 'r')
            finame = trick_name
            for fname in zfile.namelist():
                if fname.find('.DS_Store') < 0 and fname.find('__MACOSX') < 0:
                    fname1 = fname.encode("cp437").decode("utf-8")
                    if fname.endswith('/'):
                        pathname = os.path.dirname(TRICKS_PATH + fname1)
                        if not os.path.exists(pathname) and pathname != "":
                            os.makedirs(pathname)
                    else:
                        data = zfile.read(fname)
                        fo = open(TRICKS_PATH + fname1, "wb")
                        fo.write(data)
                        fo.close()
            zfile.close()

            if os.path.exists(TRICKS_PATH + finame):
                try:
                    _thread.start_new(update_bot, (finame, trick_no))
                except Exception as e:
                    # 出现异常，更新失败
                    update_trick(trick_no, False)
                    print(e)

            return str({'result': True,
                        'data': "update success"})

        else:
            return str({'result': False,
                        'data': "update error"})

    except Exception as e:
        return str({'result': False,
                    'data': str(e)})


def update_bot(finame, trick_no):
    bots_factor[finame] = Bot(TRICKS_PATH + finame)
    print("complete")
    update_trick(trick_no, True)


def update_trick(trick_no, is_success):
    if not isinstance(is_success, bool):
        is_success = False

    headers = {"token": TOKEN}
    params = {
        "salesPitchNo": trick_no,
        "isUpdate": is_success
    }
    requests.post(AUTOSERVICE_HOST + AUTOSERVISE_TRICK_UPDATE_URL, params=params, headers=headers)


@app.route("/getDialogRecord")
def check_dialog_record():
    response = Response()
    trick = request.args.get("trick")
    if trick is None:
        return str({
            "state": "error",
            "sentence": "parameter [trick] not exist."
        })
    file_names = os.listdir(TRICKS_PATH)
    if trick not in file_names:
        return str({
            "state": "error",
            "sentence": "not exist [trick]."
        })
    else:
        domain_file = os.listdir(TRICKS_PATH + '/' + trick + '/domain/')
        domain_file_info = {}
        writer = csv.writer(response.stream)
        fileHeader = ['场景', '话术文本', '录音名']
        writer.writerow(fileHeader)
        writer.writerow(["开场声音", "喂？您好～", trick + get_hash_code("喂？您好～") + '.pcm'])
        writer.writerow(["等待超时", "您能听的清楚么", trick + get_hash_code("您能听的清楚么") + '.pcm'])
        for file in domain_file:
            with open(TRICKS_PATH + '/' + trick + '/domain/' + file) as json_file:
                data = json.load(json_file)
                for k, v in data.items():
                    stage = (file.split('.')[0] + '' + k)
                    sentence = v['sentence']
                    name = trick + get_hash_code(sentence) + '.pcm'
                    domain_file_info.update({stage: sentence})
                    writer.writerow([stage, sentence, name])
            json_file.close()
        with open(TRICKS_PATH + '/' + trick + '/qa/qa.json') as qa:
            data = json.load(qa)
            for k, v in data.items():
                stage1 = 'qa' + k
                sentence1 = v['sentence']
                for k, v in domain_file_info.items():
                    stage = stage1 + '+' + k
                    sentence = sentence1 + v
                    name = trick + get_hash_code(sentence) + '.pcm'
                    writer.writerow([stage, sentence, name])
        qa.close()
    response.mimetype = 'text/csv'
    response.charset = 'UTF-8'
    response.headers = {'Content-disposition': 'attachment; filename=' + trick +
                                               datetime.datetime.today().strftime('%Y%m%d') + '.csv;'}
    return response


@app.route("/getTrick")
def get_trick():
    finames = []
    for filename in os.listdir(TRICKS_PATH):
        finames.append(filename)
    return str({'status': 'successful',
                'result': finames})


@app.route("/get_dialog_record")
def get_dialog_record():
    response = Response()
    trick = request.args.get("trick")
    file_format = request.args.get("file_format")
    if trick is None:
        return str({
            "state": "error",
            "sentence": "parameter [trick] not exist."
        })
    file_names = os.listdir(TRICKS_PATH)
    if trick not in file_names:
        return str({
            "state": "error",
            "sentence": "not exist [trick]."
        })
    else:
        domain_file = os.listdir(TRICKS_PATH + '/' + trick + '/domain/')
        domain_file_info = {}
        fileHeader = ['场景', '话术文本', '录音名']
        rows = []
        rows.append(fileHeader)
        for file in domain_file:
            with open(TRICKS_PATH + '/' + trick + '/domain/' + file) as json_file:
                data = json.load(json_file)
                for k, v in data.items():
                    stage = (file.split('.')[0] + '' + k)
                    sentence = v['sentence']
                    name = trick + get_hash_code(sentence) + '.pcm'
                    domain_file_info.update({stage: sentence})
                    rows.append([stage, sentence, name])
            json_file.close()
        with open(TRICKS_PATH + '/' + trick + '/qa/qa.json') as qa:
            data = json.load(qa)
            for k, v in data.items():
                stage1 = 'qa' + k
                sentence1 = v['sentence']
                for k, v in domain_file_info.items():
                    stage = stage1 + k
                    sentence = sentence1 + v
                    name = trick + get_hash_code(sentence) + '.pcm'
                    rows.append([stage, sentence, name])
        qa.close()

        if file_format == "csv":
            writer = csv.writer(response.stream)
            for i in rows:
                writer.writerow(i)
            response.mimetype = 'text/csv'
            response.charset = 'gbk'
            response.headers = {'Content-disposition': 'attachment; filename=' + trick +
                                                       datetime.datetime.today().strftime('%Y%m%d') + '.csv;'}
        elif file_format == "excel":
            wb = xlwt.Workbook()
            sheet = wb.add_sheet("1")
            for i in range(len(rows)):
                sheet.write(i, 0, rows[i][0])
                sheet.write(i, 1, rows[i][1])
                sheet.write(i, 2, rows[i][2])
            wb.save(response.stream)
            response.mimetype = 'application/x-xls'
            response.charset = 'gbk'
            response.headers = {'Content-disposition': 'attachment; filename=' + trick +
                                                       datetime.datetime.today().strftime('%Y%m%d') + '.xls;'}
        else:
            return str({
                "state": "error",
                "sentence": "no this file format."
            })

    return response


if __name__ == '__main__':
    app.run('0.0.0.0', 5000)
