# 中科大研究生课程成绩自动查询脚本

## 基本原理

用合适的 Cookie 向 [https://yjs1.ustc.edu.cn/gsapp/sys/wdcjapp/modules/wdcj/xscjcx.do](https://yjs1.ustc.edu.cn/gsapp/sys/wdcjapp/modules/wdcj/xscjcx.do) 发送 POST 请求即可获得 json 格式的成绩信息。Cookie 中包含两个关键字段

* `GS_SESSIONID`: 这是每一次通过统一身份认证登录 [yjs1.ustc.edu.cn](yjs1.ustc.edu.cn) 都会获得的 Session ID。
* `_WEU`: 一个神奇的字段，登录完毕后重定向到 [yjs1.ustc.edu.cn](yjs1.ustc.edu.cn) 时会获取初值。在访问 `我的成绩` 时会更新 `_WEU`，使用更新后的 `_WEU` 发送 POST 请求才能获取成绩。

## 使用方法

两种方式任选其一

### 命令行参数

* `-u`/`--uid`: 学号
* `-p`/`--password`: 统一身份认证登录的密码
* `-m`/`--mail`: 邮箱
* `-mp`/`--mail-password`: 邮箱密码
* `-s`/`--server`: 邮箱 SMTP 服务器地址 （默认为科大邮箱 `mail.ustc.edu.cn`）
* `-po`/`--port`: 邮箱 SMTP 服务端口 （默认为 465）

示例如下

```python
python3 checker.py --uid SA114514 --password 1919810 --mail username@mail.ustc.edu.cn --mail-password 123456
```

### 配置文件

上述命令行参数可通过同目录下的 `config.json` 文件传入，示例如下

```json
{
  "uid": "SA114514",
  "password": "123456",
  "mail": "username@mail.ustc.edu.cn",
  "mail_password": "123456"
}
```

```python
# 直接运行
python3 checker.py
```

### 运行效果

* 首次运行: 获取成绩后，存入 `info.json` 中，并登录你指定的邮箱向自己发送邮件，邮件主题为 `成绩更新: 课程名+课程名+...`，邮件内容是每门课的课堂号、课程名、教师、学分、分制、成绩、是否通过、成绩上传时间。
* 非首次运行: 通过 POST 请求拿到成绩后，会和 `info.json` 中存的数据比对。如果有新的课程成绩，更新 `info.json`，并向你的邮箱发送新加课程的成绩。

## 定时运行

可以使用 `systemd` 的定时器或者 python 的 `schedule` 库进行定时运行

* systemd: [Systemd 定时器教程](https://www.ruanyifeng.com/blog/2018/03/systemd-timer.html)
* schedule: [https://schedule.readthedocs.io/en/stable/](https://schedule.readthedocs.io/en/stable/)
