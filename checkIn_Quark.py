import os
import re
import sys
import time
import requests
import random

# 读取 Telegram Bot Token 和 Chat ID
TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")

def send_telegram_message(message):
    """
    发送 Telegram 通知
    """
    if TG_BOT_TOKEN and TG_CHAT_ID:
        url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": TG_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        response = requests.post(url, data=data)
        if response.status_code == 200:
            print("✅ Telegram 推送成功")
        else:
            print(f"❌ Telegram 推送失败: {response.text}")
    else:
        print("⚠️ 未配置 Telegram 通知")

# 获取环境变量 COOKIE_QUARK
def get_env():
    if "COOKIE_QUARK" in os.environ:
        return re.split(r'\n|&&', os.environ.get('COOKIE_QUARK'))
    else:
        print('❌ 未添加 COOKIE_QUARK 变量')
        sys.exit(0)

class Quark:
    def __init__(self, user_data):
        self.param = user_data

    def convert_bytes(self, b):
        units = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
        i = 0
        while b >= 1024 and i < len(units) - 1:
            b /= 1024
            i += 1
        return f"{b:.2f} {units[i]}"

    def get_growth_info(self):
        url = "https://drive-m.quark.cn/1/clouddrive/capacity/growth/info"
        querystring = {
            "pr": "ucpro",
            "fr": "android",
            "kps": self.param.get('kps'),
            "sign": self.param.get('sign'),
            "vcode": self.param.get('vcode')
        }
        response = requests.get(url=url, params=querystring).json()
        return response.get("data", False)

    def get_growth_sign(self):
        url = "https://drive-m.quark.cn/1/clouddrive/capacity/growth/sign"
        querystring = {
            "pr": "ucpro",
            "fr": "android",
            "kps": self.param.get('kps'),
            "sign": self.param.get('sign'),
            "vcode": self.param.get('vcode')
        }
        data = {"sign_cyclic": True}
        response = requests.post(url=url, json=data, params=querystring).json()
        if response.get("data"):
            return True, response["data"]["sign_daily_reward"]
        else:
            return False, response["message"]

    def do_sign(self):
        log = ""
        growth_info = self.get_growth_info()
        if growth_info:
            log += (
                f"🙍🏻‍♂️ 用户: {self.param.get('user')}\n"
                f"💾 网盘总容量: {self.convert_bytes(growth_info['total_capacity'])}，"
                f"签到累计容量: {self.convert_bytes(growth_info['cap_composition'].get('sign_reward', 0))}\n"
            )
            if growth_info["cap_sign"]["sign_daily"]:
                log += (
                    f"✅ 今日已签到: +{self.convert_bytes(growth_info['cap_sign']['sign_daily_reward'])}\n"
                    f"连签进度: ({growth_info['cap_sign']['sign_progress']}/{growth_info['cap_sign']['sign_target']})\n"
                )
            else:
                sign, sign_return = self.get_growth_sign()
                if sign:
                    log += (
                        f"✅ 今日签到成功: +{self.convert_bytes(sign_return)}\n"
                        f"连签进度: ({growth_info['cap_sign']['sign_progress'] + 1}/{growth_info['cap_sign']['sign_target']})\n"
                    )
                else:
                    log += f"❌ 签到失败: {sign_return}\n"
        else:
            raise Exception("❌ 获取成长信息失败")

        return log

def main():
    msg = ""
    cookie_quark = get_env()
    print(f"✅ 检测到 {len(cookie_quark)} 个账号")

    # 1 分钟内随机延迟执行
    delay = random.randint(10, 60)
    print(f"⏳ 随机延迟 {delay} 秒执行...")
    time.sleep(delay)

    for i, cookie in enumerate(cookie_quark):
        user_data = {}
        for a in cookie.replace(" ", "").split(';'):
            if '=' in a:
                key, value = a.split('=', 1)
                user_data[key] = value

        log = f"📌 账号 {i + 1}:\n"
        log += Quark(user_data).do_sign()
        msg += log + "\n"

    print(msg.strip())
    send_telegram_message(f"📢 夸克自动签到\n\n{msg.strip()}")

if __name__ == "__main__":
    print("---------- 夸克网盘开始签到 ----------")
    main()
    print("---------- 夸克网盘签到完毕 ----------")
