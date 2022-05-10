#!/usr/bin/python
# -*- coding: utf-8 -*-

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import time
import random
import string
import json
import re
import telegram
import requests


mypath = os.path.split(os.path.realpath(__file__))[0]
chromedriver = ""
if os.name == "nt":
    chromedriver = mypath + "\chromedriver"
elif os.name == "posix":
    chromedriver = '/usr/bin/chromedriver'

service = Service(chromedriver)
os.environ["webdriver.chrome.driver"] = chromedriver

options = webdriver.ChromeOptions()
options.add_argument('--no-sandbox')  # 解决DevToolsActivePort文件不存在的报错
options.add_argument('window-size=1920x1080')  # 指定浏览器分辨率
options.add_argument('--disable-gpu')  # 谷歌文档提到需要加上这个属性来规避bug
# chrome_options.add_argument('--hide-scrollbars') #隐藏滚动条, 应对一些特殊页面
# chrome_options.add_argument('blink-settings=imagesEnabled=false') #不加载图片, 提升速度
if os.name == "posix":
    # 浏览器不提供可视化页面. linux下如果系统不支持可视化不加这条会启动失败
    options.add_argument('--headless')

user_ag = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.74 Safari/537.36"
options.add_argument('user-agent=%s' % user_ag)

token = ''
chat_id = ''
delay = 10


# 查找元素 by class


def find_element_by_class(driver, class_name):
    return WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.CLASS_NAME, class_name)), '未找到 Class 为 "%s" 的元素' % class_name)


# 查找元素 by id


def find_element_by_id(driver, id):
    return WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.ID, id)), '未找到 id 为 "%s" 的元素' % id)


# 查找元素并且是可用状态 by class


def find_enable_by_class(driver, class_name):
    return WebDriverWait(driver, delay).until(EC.element_to_be_clickable((By.CLASS_NAME, class_name)), '元素 "%s" 不可用' % class_name)


# 发送TG消息


def sendMsg(msg):
    print(msg)
    if len(token) == 0:
        return
    bot = telegram.Bot(token=token)
    bot.send_message(chat_id=chat_id, text=msg)

# 更新网站上的密码


def update_pwd(api_host, apple_id, passwd):
    if len(api_host) == 0:
        return
    # 以下为PUT请求
    postdatas = {'apple_id': apple_id, 'passwd': passwd}
    r = requests.put(api_host, data=postdatas)
    if r.status_code == requests.codes.ok:
        sendMsg(apple_id + ' 密码更新成功！')
    else:
        sendMsg('更新密码出错啦：' + r.raise_for_status())

# 创建一个强密码


def createPwd(passwordLength):
    pw = ''
    # * 2 增加数字和特殊字符出现的概率
    str = string.digits * 2 + string.ascii_letters + '!@#$%^&*()_+=-' * 2
    while True:
        # 不包含重复字符的密码
        pw = ''.join(random.sample(str, k=passwordLength))
        # 可能包含重复字符的密码
        #pw = ''.join(random.choices(str, k=passwordLength))
        if re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)', pw):
            print("最终密码：%s" % pw)
            return pw
        else:
            print("密码：%s 强度不够" % pw)


# 解锁操作


def check_appleid(item):
    apple_id = item["id"]
    dob = item["dob"]
    qa = item["qa"]
    if len(apple_id) < 6 or len(dob) != 10 or len(qa) != 3:
        print("Aplle ID(%s) 信息有误！请检查！" % apple_id)
        return
    api_host = item["api_host"]
    last_reset_time = item["last_reset_time"]
    reset_pwd_interval = item["reset_pwd_interval"]
    now = round(time.time())
    is_reset_pwd = now - last_reset_time > reset_pwd_interval * 60
    item["status"] = 1
    try:
        driver = webdriver.Chrome(service=service, options=options)
        driver.implicitly_wait(delay)
        driver.get(
            "https://iforgot.apple.com/password/verify/appleid?language=en")
        # 等待文本框出现且可用
        id_input =  find_enable_by_class(driver, "form-textbox-input")
        id_input.click()
        id_input.send_keys(apple_id)
        # 等待按钮可点击
        find_enable_by_class(driver, "last").click()
        try:
            # 正常情况
            msg = find_element_by_class(
                driver, "subtitle").get_attribute("innerHTML")
        except Exception as e:
            # 超时未跳转
            msg = find_element_by_class(
                driver, "app-title").get_attribute("innerHTML")

        print(msg)
        # 重置密码
        if msg == "Select what information you want to reset.":
            if (not is_reset_pwd) or reset_pwd_interval < 100:
                print("时间未到，不重置密码")
                return

            print("重置密码...")
            find_enable_by_class(driver, "last").click()
            find_element_by_id(driver, 'optionquestions')
            driver.find_elements(
                by=By.CLASS_NAME, value="form-radiobutton-indicator")[1].click()
            find_enable_by_class(driver, "last").click()

            # 输入生日
            find_enable_by_class(driver, "date-input").send_keys(dob)
            time.sleep(1)
            find_enable_by_class(driver, "last").click()

            # 回答问题
            find_enable_by_class(driver, "question")
            time.sleep(1)  # 等待两个文本框出现
            questions = driver.find_elements(
                by=By.CLASS_NAME, value="question")
            answers = driver.find_elements(
                by=By.CLASS_NAME, value="security-answer")
            for i in range(len(questions)):
                answers[i].send_keys(
                    qa[questions[i].get_attribute("innerText")])
            find_enable_by_class(driver, "last").click()
            # 设置密码 createPwd
            find_element_by_id(driver, "password")
            pwd_new = createPwd(12)
            pwd_inputs = driver.find_elements(
                by=By.CLASS_NAME, value="form-textbox-input")
            pwd_inputs[0].send_keys(pwd_new)
            pwd_inputs[1].click()
            pwd_inputs[1].send_keys(pwd_new)
            time.sleep(1)
            find_enable_by_class(driver, "last").click()

            msg = apple_id + " 密码已重置为 %s " % pwd_new
            item["passwd"] = pwd_new
            item["last_reset_time"] = now
            update_pwd(api_host, apple_id, pwd_new)
            sendMsg(msg)
            time.sleep(3)
            return True
        # 解锁
        elif msg == "Select how you want to unlock your account:":
            print("正在解锁 %s ..." % apple_id)
            find_element_by_id(driver, 'optionemail')
            oq = driver.find_elements(
                by=By.CLASS_NAME, value="form-radiobutton-indicator")
            # 只能通过邮件解锁的情况
            if len(oq) == 1:
                oq[0].click()
                find_enable_by_class(driver, "last").click()
                msg = "大事不好了，%s 只能用邮件解锁，已经给你发邮件了..." % apple_id
                sendMsg(msg)
                time.sleep(2)
                return
            # 通过回答问题解锁
            oq[1].click()
            find_enable_by_class(driver, "last").click()
            find_element_by_class(driver, "date-input").send_keys(dob)
            time.sleep(1)
            find_enable_by_class(driver, "last").click()
            # 回答问题
            find_enable_by_class(driver, "question")
            time.sleep(1)  # 等待两个文本框出现
            questions = driver.find_elements(
                by=By.CLASS_NAME, value="question")
            answers = driver.find_elements(
                by=By.CLASS_NAME, value="security-answer")
            for i in range(len(questions)):
                answers[i].send_keys(
                    qa[questions[i].get_attribute("innerText")])
            time.sleep(1)
            find_enable_by_class(driver, "last").click()
            # 解锁并修改密码
            find_element_by_class(driver, "pwdChange").click()
            # 等待密码框出现
            find_element_by_id(driver, "password")
            pwd_new = createPwd(12)
            pwd_inputs = driver.find_elements(
                by=By.CLASS_NAME, value="form-textbox-input")
            pwd_inputs[0].send_keys(pwd_new)
            pwd_inputs[1].click()
            pwd_inputs[1].send_keys(pwd_new)
            time.sleep(1)
            find_enable_by_class(driver, "last").click()
            time.sleep(2)
            find_enable_by_class(driver, "last").click()
            find_element_by_class(driver, "done")

            msg = apple_id + " 已解锁，新密码 %s " % pwd_new
            item["passwd"] = pwd_new
            item["last_reset_time"] = now
            update_pwd(api_host, apple_id, pwd_new)
            sendMsg(msg)
            time.sleep(3)
            return True
        # 双重认证
        elif msg == "Confirm your phone number.":
            print("正在关闭 %s 的双重认证..." % apple_id)
            find_element_by_class(driver, "button-caption-link").click()
            driver.find_elements(by=By.CLASS_NAME, value="last")[1].click()
            #driver.find_element(by=By.XPATH, value="/html/body/div[5]/div/div/recovery-unenroll-start/div/idms-step/div/div/div/div[3]/idms-toolbar/div/div/div/button[1]").click()
            # 输入生日
            find_element_by_class(driver, "date-input").send_keys(dob)
            find_enable_by_class(driver, "last").click()
            # 回答问题
            find_element_by_class(driver, "question")
            time.sleep(2)
            questions = driver.find_elements(
                by=By.CLASS_NAME, value="question")
            answers = driver.find_elements(
                by=By.CLASS_NAME, value="form-textbox-input")
            for i in range(len(questions)):
                answers[i].send_keys(
                    qa[questions[i].get_attribute("innerText")])
            find_enable_by_class(driver, "last").click()
            time.sleep(3)
            find_enable_by_class(driver, "last").click()
            time.sleep(3)
            # 设置密码 createPwd
            pwd_new = createPwd(12)
            pwd_inputs = driver.find_elements(
                by=By.CLASS_NAME, value="form-textbox-input")
            pwd_inputs[0].send_keys(pwd_new)
            pwd_inputs[1].click()
            pwd_inputs[1].send_keys(pwd_new)
            find_enable_by_class(driver, "last").click()
            find_element_by_class(driver, "idms-modal-content")
            time.sleep(1)
            driver.find_elements(by=By.CLASS_NAME, value="last")[1].click()

            msg = apple_id + " 双重认证已关闭，新密码 %s " % pwd_new
            item["passwd"] = pwd_new
            item["last_reset_time"] = now
            update_pwd(api_host, apple_id, pwd_new)
            sendMsg(msg)
            time.sleep(3)
            return True
        # 验证未通过(错误)
        elif msg == "Having trouble signing in?":
            msg = find_element_by_class(
                driver, "form-message").get_attribute("innerHTML").strip()
            if msg == 'Your request could not be completed because of an error. Try again later.':
                msg = msg + '(建议换个不同运营商的VPS尝试)'
            sendMsg("出错啦！" + msg)
            item["status"] = 0
            return
        else:
            print("我无法理解")
    except Exception as e:
        msg = '检查 %s 时，超时了。%s' % (apple_id, str(e))
        item["status"] = 0
        sendMsg(msg)
    finally:        
        driver.quit()


apple_data = []
config = {}
save = False
with open(mypath + '/config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)
token = config.get('token')
chat_id = config.get('chat_id')
apple_ids = config.get('apple_id')
for i, item in enumerate(apple_ids):
    print('正在检查 %s ...' % item["id"])
    flag = check_appleid(item)
    if flag:
        save = flag
    # str_time = time.strftime(u"%Y年%m月%d日 %H:%M:%S",time.localtime(item['last_reset_time']))
    str_time = time.strftime(u"%Y年%m月%d日 %H:%M:%S",
                             time.localtime(round(time.time())))
    apple_data.append({"id": item['id'], "passwd": item['passwd'],
                      "status": item["status"], "last_reset_time": str_time})
    print('暂停10秒')
    time.sleep(10)

# 构造一个 json 数据，供静态 HTML 使用
print('正在写入 JSON 数据...')
with open(mypath + '/data.json', 'w', encoding='utf-8') as f:
    json.dump(apple_data, f, indent=4)
if save:
    print('正在更新 config 数据...')
    with open(mypath + '/config.json', 'w') as f:
        json.dump(config, f, indent=4)

print("执行完成！即将退出...")
time.sleep(3)
