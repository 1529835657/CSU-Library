import json
import random
import base64
import pandas
import logging
import requests
import argparse
import configparser

from bs4 import BeautifulSoup
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import pad


def randomString(length):
    '''
    获取随机字符串
    :param length:随机字符串长度
    '''
    ret_string = ''
    aes_chars = 'ABCDEFGHJKMNPQRSTWXYZabcdefhijkmnprstwxyz2345678'
    for i in range(length):
        ret_string += random.choice(aes_chars)
    return ret_string


def getAesString(data, key, iv):
    '''
    用AES-CBC方式加密字符串
    :param data: 需要加密的字符串
    :param key: 密钥
    :param iv: 偏移量
    :return: base64格式的加密字符串
    '''
    # 预处理字符串
    data = str.encode(data)
    data = pad(data, AES.block_size)

    # 预处理密钥和偏移量
    key = str.encode(key)
    iv = str.encode(iv)

    # 初始化加密器
    cipher = AES.new(key, AES.MODE_CBC, iv)
    cipher_text = cipher.encrypt(data)

    # 返回的是base64格式的密文
    cipher_b64 = str(base64.b64encode(cipher_text), encoding='utf-8')
    return cipher_b64


class CSULibrary(object):
    client = requests.Session()

    def __init__(self, userid, password):
        seat_data = pandas.read_csv('seat.csv')
        self.userid = userid
        self.password = password
        config = configparser.ConfigParser()
        config.read('config.ini')
        self.seatno = eval(config["DATABASE"]["SEAT"])
        self.area = []
        self.seatid = []
        for s in self.seatno:
            self.area.append(seat_data[seat_data["NO"] == s].values[0][2])
            self.seatid.append(seat_data[seat_data["NO"] == s].values[0][0])

    def login(self):
        '''
        做任何操作前都要先登录以获得cookie
        '''
        url1 = "http://libzw.csu.edu.cn/cas/index.php"
        params1 = {
            "callback": "http://libzw.csu.edu.cn/home/web/f_second"
        }
        response1 = self.client.get(url1, params=params1)

        soup = BeautifulSoup(response1.text, 'html.parser')
        salt = soup.find('input', id="pwdEncryptSalt")['value']
        execution = soup.find('input', id="execution")['value']

        url2 = "https://ca.csu.edu.cn/authserver/login?service=http%3A%2F%2Flibzw.csu.edu.cn%2Fcas%2Findex.php%3Fcallback%3Dhttp%3A%2F%2Flibzw.csu.edu.cn%2Fhome%2Fweb%2Ff_second"
        headers2 = {
            'cache-control': 'max-age=0',
            'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="100", "Google Chrome";v="100"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'upgrade-insecure-requests': '1',
            'origin': 'https://ca.csu.edu.cn',
            'content-type': 'application/x-www-form-urlencoded',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-user': '?1',
            'sec-fetch-dest': 'document',
            'referer': 'https://ca.csu.edu.cn/authserver/login?service=http%3A%2F%2Flibzw.csu.edu.cn%2Fcas%2Findex.php%3Fcallback%3Dhttp%3A%2F%2Flibzw.csu.edu.cn%2Fhome%2Fweb%2Ff_second',
        }
        data2 = {
            'username': self.userid,
            'password': getAesString(randomString(64)+self.password, salt, randomString(16)),
            'captcha': '',
            '_eventId': 'submit',
            'cllt': 'userNameLogin',
            'dllt': 'generalLogin',
            'lt': '',
            'execution': execution
        }
        response2 = self.client.post(url2, headers=headers2, data=data2)

    def reserve(self):
        '''
        预约指定位置,返回结果消息
        '''
        self.login()

        access_token = requests.utils.dict_from_cookiejar(self.client.cookies)[
            'access_token']

        for i in range(0, len(self.seatid)):
            url = "http://libzw.csu.edu.cn/api.php/spaces/" + \
                str(self.seatid[i])+"/book"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36',
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': 'http://libzw.csu.edu.cn/home/web/seat/area/1',
            }
            data = {
                'access_token': access_token,
                'userid': self.userid,
                'segment': self.getBookTimeId(i)[1],
                'type': '1',
                'operateChannel': '2'
            }
            response = self.client.post(url, headers=headers, data=data)
            if response.json()['status'] == 1:
                break

        if response.json()['status'] == 0:
            raise Exception(response.json()['msg'])
        logging.info(response.json()['msg'])

    def checkIn(self):
        '''
        获取您的预约信息并签到,返回结果消息
        '''
        status = self.getCurrentUse()['statusname']
        if status != '已预约' and status != '临时离开':
            raise Exception("当前座位状态不应当签到")

        self.login()

        access_token = requests.utils.dict_from_cookiejar(self.client.cookies)[
            'access_token']
        seat_id = str(self.getCurrentUse()['id'])
        url = "http://libzw.csu.edu.cn/api.php/profile/books/"+seat_id
        headers = {
            'Referer': 'http://libzw.csu.edu.cn/home/web/seat/area/1',
        }
        data = {
            'id': seat_id,
            '_method': 'checkin',
            'access_token': access_token,
            'userid': self.userid,
            'operateChannel': '3'
        }
        response = self.client.post(url, headers=headers, data=data)
        logging.info(response.json()['msg'])

    def leave(self):
        '''
        获取您正在使用的座位信息并签到,返回结果消息
        '''
        status = self.getCurrentUse()['statusname']
        if status != '使用中':
            raise Exception("当前座位状态不应当签离")

        self.login()

        access_token = requests.utils.dict_from_cookiejar(self.client.cookies)[
            'access_token']
        seat_id = str(self.getCurrentUse()['id'])
        url = "http://libzw.csu.edu.cn/api.php/profile/books/"+seat_id
        headers = {
            'Referer': 'http://libzw.csu.edu.cn/home/web/seat/area/1',
        }
        data = {
            'id': seat_id,
            '_method': 'checkout',
            'access_token': access_token,
            'userid': self.userid,
            'operateChannel': '3'
        }
        response = self.client.post(url, headers=headers, data=data)
        logging.info(response.json()['msg'])

    def getCurrentUse(self):
        '''
        获取正在使用中的座位或研讨间,返回内容较为复杂,建议自己发包自行查看response
        '''
        url = "http://libzw.csu.edu.cn/api.php/currentuse"
        headers = {
            "Referer": "http://libzw.csu.edu.cn/home/web/seat/area/1"
        }
        params = {
            "user": self.userid
        }
        response = requests.get(url, headers=headers, params=params)
        if len(response.json()['data']) == 0:
            raise Exception("当前没有正在使用中的座位或研讨间")
        return response.json()['data'][0]

    def getBookTimeId(self, i):
        '''
        每天每个区域都有一个独特的bookTimeId(预约时间ID)
        该函数返回今天和明天的bookTimeId
        :param i: area是一个区域数组,i指示我们获取第几位元素的bookTimeId
        '''
        url = "http://libzw.csu.edu.cn/api.php/v3areadays/"+str(self.area[i])
        headers = {
            'Referer': 'http://libzw.csu.edu.cn/home/web/seat/area/1'
        }
        response = requests.get(url, headers=headers)
        return response.json()["data"]["list"][0]["id"], response.json()["data"]["list"][1]["id"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='CSU图书馆')

    parser.add_argument('--action', type=str, help='操作类型')
    parser.add_argument('--userid', type=str, help='账号')
    parser.add_argument('--password', type=str, help='密码')
    args = parser.parse_args()

    LOG_FORMAT = "%(asctime)s\t%(levelname)s\t%(message)s"
    logging.basicConfig(filename='library.log',
                        level=logging.INFO, format=LOG_FORMAT)

    helper = CSULibrary(args.userid, args.password)
    try:
        if args.action == 'reserve':
            helper.reserve()
        elif args.action == 'checkIn':
            helper.checkIn()
        elif args.action == 'leave':
            helper.leave()
    except Exception as e:
        logging.error(e)