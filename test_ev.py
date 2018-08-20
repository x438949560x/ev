# coding:utf-8


import requests
import json
import datetime
import os
import smtplib
from email.mime.text import MIMEText
import hashlib
import time


user_info = {}
user_name = ''
pwd = ''
time_gap = 5
receiver = ''
continues_play_gap = 60
continues_play_max = 10
play_max_day = 20
size = 10
recall = True


def load_config():
    with open('config.txt', 'r') as f:
        try:
            lines = f.readlines()
            global user_name
            global pwd
            global time_gap
            global receiver
            global continues_play_gap
            global continues_play_max
            global play_max_day
            global size
            global recall
            user_name = lines[0].split('\n')[0].split('=')[1].split('\'')[1]
            pwd = lines[1].split('\n')[0].split('=')[1].split('\'')[1]
            if not user_name or not pwd:
                raise Exception("请按规则输入账号密码")
            time_gap = lines[2].split('\n')[0].split('=')[1]
            time_gap = int(time_gap)
            receiver = lines[3].split('\n')[0].split('=')[1].split('\'')[1]
            continues_play_gap = lines[4].split('\n')[0].split('=')[1]
            continues_play_gap = int(continues_play_gap)
            continues_play_max = lines[5].split('\n')[0].split('=')[1]
            continues_play_max = int(continues_play_max)
            play_max_day = lines[6].split('\n')[0].split('=')[1]
            play_max_day = int(play_max_day)
            size = lines[7].split('\n')[0].split('=')[1]
            size = int(size)
            recall = lines[8].split('\n')[0].split('=')[1]
            recall = bool(recall)
            if time_gap <= 0 or continues_play_max <= 0 or play_max_day <= 0 or size <= 0 or continues_play_gap <= 0 or recall is None:
                raise Exception("加载错误，注意输入的值不要小于0，检查配置recall时是否填写错误!")
        except IOError as e:
            print(e)
            print("load error!")


def login():
    headers = {
'Accept': 'application/json, text/plain, */*',
'Accept-Encoding': 'gzip, deflate',
'Accept-Language': 'zh-CN,zh;q=0.9',
'Content-Length': '92',
'Content-Type': 'application/json;charset=UTF-8',
'Cookie': 'user_name=%s; password=%s' % (user_name, pwd),
'Host': 'cer.ieway.cn',
'Origin': 'http://cer.ieway.cn',
'Proxy-Connection': 'keep-alive',
'Referer': 'http://cer.ieway.cn/login?from=/cer',
'token': '[object Object]',
'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36'
}
    m = hashlib.md5()
    m.update(str.encode(pwd, encoding='utf-8'))
    sign = m.hexdigest()
    data = {"user_name":user_name,"user_pwd":sign,"deviceType":False}
    data = json.dumps(data, separators=(',', ':'))
    r = requests.post('http://cer.ieway.cn/api/v1/user/cloginChecked', data=data, headers=headers)
    token = json.loads(r.content)['result']['token']
    return token


def get_evToken(token):
    headers = {
'Accep':'application/json, text/plain, */*',
'Accept-Encoding':'gzip, deflate',
'Accept-Language':'zh-CN,zh;q=0.8',
'Content-Length':'92',
'Content-Type':'application/json;charset=UTF-8',
'Cookie':'user_name=%s; password=%s; token=%s' % (user_name, pwd, token),
'Host':'cer.ieway.cn',
'Origin':'http://cer.ieway.cn',
'Proxy-Connection':'keep-alive',
'Referer':'http://cer.ieway.cn/cer',
'token':token,
'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'
}
    m = hashlib.md5()
    m.update(str.encode(pwd, encoding='utf-8'))
    sign = m.hexdigest()
    data = {"user_name":user_name,"user_pwd":sign,"deviceType":False}
    data = json.dumps(data, separators=(',', ':'))
    r = requests.get('http://cer.ieway.cn/api/v1/ev2/login/getEvToken', headers=headers, data=data)
    id = json.loads(r.content)['acc_info']['id']
    evToken = json.loads(r.content)['token']
    cookie = 'user_name=%s; password=%s; token=%s; account_id=%s; evtoken=%s' % (user_name, pwd, token, id, evToken)
    if cookie:
        print("登陆成功!")
    return cookie


def crawler_records(cookie):
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'Cookie': cookie,
        'Host': 'cer.ieway.cn',
        'If-Modified-Since': 'Fri, 17 Aug 2018 11:00:59 GMT',
        'If-None-Match': 'W/"5b76aaeb-d2f"',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36'
    }

    html = requests.get("http://cer.ieway.cn/api/v1/user/mng/certificate/getCrtList", headers=headers)
    html = str(html.content, "utf-8")
    json_obj = json.loads(html)
    recordsTotal = json_obj['result']['recordsTotal']
    total_records = requests.get("http://cer.ieway.cn/api/v1/user/mng/certificate/getCrtList?page=1&pageSize=%s" % size, headers=headers)  # str(int(recordsTotal)*10)
    total_reocrds_json = str(total_records.content, "utf-8")
    json_obj2 = json.loads(total_reocrds_json)
    if json_obj2:
        print("拉取数据成功!")
    return json_obj2


def online_monitor(json_obj2):
    """
    拉一遍初始数据(激活的用户的数据)
    """
    for i in json_obj2['result']['list']:
        if i['state'] == 1:
           for files in os.walk('Logs'):
               if i['code'] not in files[2]:
                   user_info[i['code']] = i['left_times']
                   with open('Logs/'+str(i['code']), 'a+') as f:
                       now = datetime.datetime.now()
                       left_times = i['left_times']
                       id = i['id']
                       result = "%s-%s-%s" % (str(now), str(left_times), str(id))
                       f.write(result+'\n')
                   print("初始化数据成功!")


def update_records(json_obj):
    """每隔一定周期重新拉取一遍数据做更新"""
    if not user_info:
        for files in os.walk('Logs'):
            for file in files[2]:
                with open('Logs/'+file, 'r') as f:
                    lines = f.readlines()
                    rows = len(lines)
                    user_info[file] = lines[rows-1].split('-')[3].split('\n')[0]
    for i in json_obj['result']['list']:
        if i['state'] == 1 and user_info.get(i['code']) and int(i['left_times']) != int(user_info.get(i['code'])):
            user_info[i['code']] = i['left_times']
            with open('Logs/' + str(i['code']), 'a+') as f:
                now = datetime.datetime.now()
                left_times = i['left_times']
                result = "%s-%s" % (str(now), str(left_times))
                f.write(result + '\n')


def warnning_email(cookie):
    """监测异常"""
    print("---异常监测中---")
    for files in os.walk('Logs'):
        for file in files[2]:
            with open('Logs/' + file, 'r') as f:
                lines = f.readlines()
                year = ''
                count = 0  # 播放时间间隔的差距
                count2 = 0  # 一天内播放次数的统计
                for line in lines:
                    years = line.split('\n')[0].split('-')[0]
                    id = line.split('\n')[0].split('-')[4]
                    months = line.split('\n')[0].split('-')[1]
                    days = line.split('\n')[0].split('-')[2].split()[0]
                    hours = line.split('\n')[0].split('-')[2].split()[1].split(':')[0]
                    minites = line.split('\n')[0].split('-')[2].split()[1].split(':')[1]
                    seconds = line.split('\n')[0].split('-')[2].split()[1].split(':')[2]
                    if not year:
                        year = years
                        global month
                        month = months
                        global day
                        day = days
                        global hour
                        hour = int(hours) * 60 * 60
                        global minite
                        minite = int(minites) * 60
                        global second
                        second = float(seconds)
                        global time_stamp
                        time_stamp = hour + minite + second
                        count2 += 1
                    else:
                        year2 = years
                        month2 = months
                        day2 = days
                        hour2 = int(hours) * 60 * 60
                        minite2 = int(minites) * 60
                        second2 = float(seconds)
                        time_stamp2 = hour2 + minite2 + second2
                        if int(year2) == int(year) and int(month2) == int(month) and int(day2) == int(day):
                            count2 += 1
                            diff = time_stamp2 - time_stamp
                            if diff < continues_play_gap:
                                count += 1
                            if count >= continues_play_max:
                                text = "该激活码连续播放次数过多！！！"
                                send_email(file, text)
                            if count2 >= play_max_day:
                                text = "该激活码今天播放次数过多！！！"
                                send_email(file, text)
                                if recall:
                                    call_code(int(id), str(file), cookie)
                        year, month, day, hour, minite, second = year2, month2, day2, hour2, minite2, second2


def send_email(code_name, text):
    mail_host = "smtp.sina.cn"
    mail_user = "15274925624@sina.cn"
    mail_pass = "Alz745631289"

    sender = '15274925624@sina.cn'
    receivers = [receiver]

    content = code_name + text
    title = 'EV异常警告'
    message = MIMEText(content, 'plain', 'utf-8')
    message['From'] = "{}".format('EV监听')
    message['To'] = ",".join(receivers)
    message['Subject'] = title

    try:
        smtpObj = smtplib.SMTP_SSL(mail_host, 465)
        smtpObj.login(mail_user, mail_pass)
        smtpObj.sendmail(sender, receivers, message.as_string())
        print("send success!")
    except smtplib.SMTPException:
        print("Error: Can't send email!")


def call_code(id, code, cookie):
    """一天内播放次数过多，召回激活码"""
    headers = {
    'Accept': 'application/json, text/plain, */*',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Connection': 'keep-alive',
    'Content-Length': '47',
    'Content-Type': 'application/json;charset=UTF-8',
    'Cookie': cookie,
    'Host': 'cer.ieway.cn',
    'Origin': 'http://cer.ieway.cn',
    'Referer': 'http://cer.ieway.cn/cer?page=1&pageSize=1055',
    'token': cookie.split(';')[2].split()[0][6:],
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36'
    }
    payload = {'id': id, 'code': code}
    data = json.dumps(payload, separators=(',', ':'))
    r = requests.post('http://cer.ieway.cn/api/v1/user/mng/certificate/sendToBlack', data=data, headers=headers)
    print("召回激活码成功!")


if __name__ == '__main__':
    load_config()
    s = datetime.datetime.now()
    token = login()
    cookie = get_evToken(token)
    while True:
        json_obj = crawler_records(cookie)
        online_monitor(json_obj)
        update_records(json_obj)
        warnning_email(cookie)
        time.sleep(time_gap)
        timer = datetime.datetime.now()
        result = (timer - s).seconds
        if result > 14400:
            token = login()
            cookie = get_evToken(token)
