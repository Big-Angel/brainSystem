FROM daocloud.io/python:3-onbuild

MAINTAINER wuyingqiang 147036scofield@gmail.com

WORKDIR /root/app

ADD ./sell_assistant ./sell_assistant
ADD ./cfgs ./cfgs
ADD ./requirements.txt ./requirements.txt

EXPOSE 5000

RUN pip install --no-cache-dir -r ./requirements.txt

WORKDIR /root/app/sell_assistant

CMD ["python", "./autobot.py"]