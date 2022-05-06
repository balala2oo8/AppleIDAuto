
 基于安全问题实现自动解锁 Apple ID 等功能
 
# 功能
- 自动解锁Apple ID
- 自动关闭双重认证
- 定时修改密码
- 修改密码后 API 请求
- tg 消息推送

# 配置文件详解(config.json)
名称 | 定义 | 说明
:- | :- | :-
token | tg 机器人token | 如果为空，不会推送tg消息
chat_id | tg 用户userid | 如果为空，不会推送tg消息
apple_id | Apple ID数组 | JSON对象数组，示例：<br>[ object, object, ... ]

### 参数 apple_id
名称 | 定义 | 说明
:- | :- | :-
id | AppleID | 如果为空则不检查
passwd | AppleID密码 | 可空
dob | 生日 | 此AppleID对应的生日，格式 MM/dd/YYYY
qa | 安全问题及答案 | 一个JSON对象，示例：<br>{"你的出生地在哪里？":"Azsx12","你的？":"WSxedc1"}<br>问题建议复制粘贴
last_reset_time | 上次更新密码的时间戳(秒) | 默认0，不能为空
reset_pwd_interval | 修改密码的间隔(分钟) | 如果大于100，那么即使没有被锁定，也会间隔此时间修改密码。建议>300，不建议设置太短
status | 账号状态 | 默认1
api_host | api地址 | 如果此项不为空，会在修改密码后请求此地址<br>请求方式：PUT<br>请求参数：{'apple_id': apple_id, 'passwd': passwd}

# 使用方法
- 要求 Python 3.7+
- 已在 Windows 11、Debian 10+ 上测试

#### Debian 10

- 在宝塔新建一个网站
- 进入网站目录
- 下载代码 
```
git clone https://github.com/balala2oo8/AppleIDAuto.git .
```
- 安装依赖
```
apt update
apt install -y python3-pip chromium-driver
pip3 install -r requirements.txt
```
- 运行
```
//测试
python3 main.py
//定时运行
crontab -e
//每30分钟运行一次
*/30 * * * * python3 /你的网站目录/main.py
``` 
- Nginx 网站配置
```
    # 限制访问来源，防止白嫖
    valid_referers *.yourdomain.web;
	  if ($invalid_referer) {
		  return 404;
    }
```

# 其他
- 没搞过 Python，代码是现抄现学，凑合着用

# 感谢

* Apple-ID-Auto：https://github.com/iSteal-it/Apple-ID-Auto
* Baidu: https://www.baidu.com 
* Google: https://www.google.com