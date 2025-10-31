import os
import re
import sys
import requests

# 从环境变量读取 Telegram Bot Token 和 Chat ID
TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")

def send(title, message):
    """
    自定义通知函数，支持控制台打印与 Telegram 推送
    """
    print(f"{title}: {message}")
    if TG_BOT_TOKEN and TG_CHAT_ID:
        send_telegram_message(title, message)
    else:
        print("⚠️ 未配置 Telegram 环境变量，跳过推送。")

def send_telegram_message(title, message):
    """
    发送 Telegram 消息（使用纯文本框样式）
    """
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    text = f"📢 {title}\n\n{message}"
    payload = {
        "chat_id": TG_CHAT_ID,
        "text": text,
        "parse_mode": "None"
    }
    try:
        res = requests.post(url, json=payload)
        if res.status_code == 200:
            print("✅ Telegram 推送成功！")
        else:
            print(f"❌ Telegram 推送失败：{res.text}")
    except Exception as e:
        print(f"❌ Telegram 推送异常：{e}")

def get_env():
    if "COOKIE_QUARK" in os.environ:
        cookie_list = re.split('\n|&&', os.environ.get('COOKIE_QUARK'))
    else:
        print('❌未添加COOKIE_QUARK变量')
        send('夸克自动签到', '❌未添加COOKIE_QUARK变量')
        sys.exit(0)
    return cookie_list


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
            return False, response.get("message", "未知错误")

    def do_sign(self):
        growth_info = self.get_growth_info()
        if not growth_info:
            raise Exception("❌ 签到异常: 获取成长信息失败")

        username = self.param.get('user', '未知用户')
        is_vip = "88VIP" if growth_info['88VIP'] else "普通用户"
        total_capacity = self.convert_bytes(growth_info['total_capacity'])
        sign_reward = self.convert_bytes(growth_info['cap_composition'].get('sign_reward', 0))

        if growth_info["cap_sign"]["sign_daily"]:
            today_reward = self.convert_bytes(growth_info['cap_sign']['sign_daily_reward'])
            progress = f"{growth_info['cap_sign']['sign_progress']}/{growth_info['cap_sign']['sign_target']}"
            sign_status = f"✅ 今日已签到 +{today_reward}"
        else:
            sign, sign_return = self.get_growth_sign()
            if sign:
                today_reward = self.convert_bytes(sign_return)
                progress = f"{growth_info['cap_sign']['sign_progress'] + 1}/{growth_info['cap_sign']['sign_target']}"
                sign_status = f"✅ 执行签到 +{today_reward}"
            else:
                progress = "—"
                sign_status = f"❌ 签到异常: {sign_return}"

        # 🔸 文本框格式（样板1）
        msg = (
            f"╔══════════ 夸克签到结果 ═════════╗\n"
            f"👤 用户：{username}\n"
            f"💎 等级：{is_vip}\n"
            f"💾 总容量：{total_capacity}\n"
            f"🎁 累计奖励：{sign_reward}\n"
            f"📅 今日签到：{sign_status}\n"
            f"📈 连签进度：{progress}\n"
            f"╚═══════════════════════════════╝\n"
        )
        return msg


def main():
    msg = ""
    cookie_quark = get_env()
    print("✅ 检测到共", len(cookie_quark), "个夸克账号\n")

    for i, cookie in enumerate(cookie_quark):
        user_data = {}
        for a in cookie.replace(" ", "").split(';'):
            if not a == '':
                k, v = a.split('=', 1)
                user_data[k] = v

        log = Quark(user_data).do_sign()
        msg += f"🙍🏻‍♂️ 第{i + 1}个账号\n{log}\n"

    send('夸克自动签到成功 ✅', msg)
    return msg


if __name__ == "__main__":
    print("----------夸克网盘开始签到----------")
    main()
    print("----------夸克网盘签到完毕----------")
