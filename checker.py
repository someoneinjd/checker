import argparse
import json
import os
import re
import requests
import sys
import smtplib

from dataclasses import asdict, dataclass, fields
from email.message import EmailMessage
from ssl import create_default_context
from typing import Any, ClassVar
from urllib.parse import unquote


@dataclass
class ClassInfo:
    FEILD_MAPPING: ClassVar[dict[str, Any]] = {
        "id": "KCDM",
        "name": "KCMC",
        "teacher_name": "LRRXM",
        "mark_system": "CJFZDM_DISPLAY",
        "credit": "XF",
        "score": "DYBFZCJ",
        "passed": "CJJL_DISPLAY",
        "upload_time": "CZSJ",
    }
    id: str
    name: str
    teacher_name: str
    mark_system: str
    credit: float
    score: float
    passed: str
    upload_time: str

    def __str__(self) -> str:
        return f"""
课堂号: {self.id}
课程名: {self.name}
教师: {self.teacher_name}
分制: {self.mark_system}
学分: {self.credit}
分数: {self.score}
是否通过: {self.passed}
分数上传时间: {self.upload_time}
"""


def from_dict(
    data: list[dict[str, Any]],
    id: str,
    name: str,
    teacher_name: str,
    mark_system: str,
    credit: str,
    score: str,
    passed: str,
    upload_time: str,
) -> list[ClassInfo]:
    return [
        ClassInfo(
            id=i[id],
            name=i[name],
            teacher_name=i[teacher_name],
            mark_system=i[mark_system],
            credit=i[credit],
            score=i[score],
            passed=i[passed],
            upload_time=i[upload_time],
        )
        for i in data
    ]


def diff(old: list[ClassInfo], new: list[ClassInfo]) -> list[ClassInfo]:
    old_ids = set(i.id for i in old)
    return list(filter(lambda i: i.id not in old_ids, new))


class Fetch:
    def __init__(self, stuid: str, password: str):
        self.session = requests.Session()
        self.stuid = stuid
        self.password = password
        self.service = "http%3A%2F%2Fyjs1.ustc.edu.cn%2Fgsapp%2Fsys%2Fyjsemaphome%2Fportal%2Findex.do%3FforceCas%3D1"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36"
        }

    def _passport(self) -> requests.Response:
        data = self.session.get(
            "https://passport.ustc.edu.cn/login?service=" + self.service,
            headers=self.headers,
        )
        data = data.text
        data = data.encode("ascii", "ignore").decode("utf-8", "ignore")
        CAS_LT = re.search(r"\$\(\"#CAS_LT\"\)\.val\(\"(\S+)\"\)", data).groups()[0]
        data = {
            "model": "uplogin.jsp",
            "service": unquote(self.service),
            "warn": "",
            "showCode": "",
            "username": self.stuid,
            "password": self.password,
            "button": "",
            "CAS_LT": CAS_LT,
        }
        return self.session.post(
            "https://passport.ustc.edu.cn/login",
            data=data,
            headers=self.headers,
            allow_redirects=False,
        )

    def get_json(self) -> list[dict[str, Any]]:
        try:
            ticket = self._passport().headers["Location"]
            # get session id && weu
            self.session.get(ticket, headers=self.headers)
        except Exception:
            print("Login Failed!", file=sys.stderr)
            print(
                f"Please check your uid ({self.stuid}) and password ({self.password}).",
                file=sys.stderr,
            )
            exit(0)
        # update weu
        self.session.get("https://yjs1.ustc.edu.cn/gsapp/sys/wdcjapp/*default/index.do")
        classes = json.loads(
            self.session.post(
                "https://yjs1.ustc.edu.cn/gsapp/sys/wdcjapp/modules/wdcj/xscjcx.do"
            ).content
        )
        return classes["datas"]["xscjcx"]["rows"]


def send_mail(
    diffs: list[ClassInfo], mail: str, mail_password: str, smtp_server: str, port: int
):
    if len(diffs) == 0:
        return
    else:
        msg = EmailMessage()
        msg["Subject"] = "成绩更新: " + "+".join(i.name for i in diffs)
        msg["From"] = mail
        msg["To"] = mail
        msg.set_content("".join(str(i) for i in diffs))

        ctx = create_default_context()
        ctx.set_ciphers("DEFAULT")
        with smtplib.SMTP_SSL(smtp_server, port, context=ctx) as server:
            server.login(mail, mail_password)
            server.send_message(msg)


def run(
    uid: str,
    password: str,
    mail: str,
    mail_password: str,
    smtp_server: str = "mail.ustc.edu.cn",
    port: int = 465,
):
    diffs: list[ClassInfo] = []
    if os.path.exists("info.json"):
        old = from_dict(
            json.load(open("info.json")),
            **{field.name: field.name for field in fields(ClassInfo)},
        )
        new = from_dict(Fetch(uid, password).get_json(), **ClassInfo.FEILD_MAPPING)
        diffs = diff(old, new)
        json.dump([asdict(i) for i in new], open("info.json", "w"))
    else:
        diffs = from_dict(Fetch(uid, password).get_json(), **ClassInfo.FEILD_MAPPING)
        json.dump([asdict(i) for i in diffs], open("info.json", "w"))
    send_mail(diffs, mail, mail_password, smtp_server, port)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="checker",
        description="Check if your scores are updated and send an email.",
    )
    parser.add_argument("-u", "--uid", type=str, help="Your student id")
    parser.add_argument("-p", "--password", type=str, help="Your password")
    parser.add_argument("-m", "--mail", type=str, help="Your email address")
    parser.add_argument("-mp", "--mail_password", type=str, help="Your email password")
    parser.add_argument(
        "-s",
        "--server",
        type=str,
        help="Your email's smtp server address (default: mail.ustc.edu.cn)",
        default="mail.ustc.edu.cn",
    )
    parser.add_argument(
        "-po",
        "--port",
        type=int,
        help="Your email's smtp server port (default: 465)",
        default=465,
    )

    if os.path.exists("config.json"):
        run(**json.load(open("config.json")))
    else:
        args = parser.parse_args()
        run(
            args.uid,
            args.password,
            args.mail,
            args.mail_password,
            args.server,
            args.port,
        )
