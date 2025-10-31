import os
import re
import sys
import time
import traceback
import requests
from datetime import datetime, timedelta

# ================== Telegram 通知配置 ==================
TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")


# ================== 推送与日志函数 ==================
def send(title, message, success=True):
    """
    控制台输出 + Telegram 通知
    """
    print(f"{title}:\n{message}")
    if TG_BOT_TOKEN and TG_CHAT_ID:
        send_telegram_message(title, message, success)
    else:
        print("⚠️ 未配置 Telegram 环境变量，跳过推送。")


def send_telegram_message(title, message, success=True):
    """
    发送 Telegram 消息
    """
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    icon = "✅" if success else "❌"
    text = f"{icon} {title}\n\n{message}"

    payload = {
        "chat_id": TG_CHAT_ID,
        "text": text,
        "parse_mode": "None"
    }
    try:
        res = requests.post(url, json=payload, timeout=10)
        if res.status_code == 200:
            print("✅ Telegram 推送成功！")
        else:
            print(f"❌ Telegram 推送失败：{res.text}")
    except Exception as e:
        print(f"❌ Telegram 推送异常：{e}")


# ================== 核心签到逻辑 ==================
def get_env():
    if "COOKIE_QUARK" in os.environ:
        cookie_list = re.split('\n|&&', os.environ.get('COOKIE_QUARK'))
    else:
        print('❌ 未添加 COOKIE_QUARK 环境变量')
        send('夸克自动签到', '❌ 未添加 COOKIE_QUARK 环境变量', success=False)
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
        try:
            response = requests.get(url=url, params=querystring, timeout=10).json()
            return response.get("data", False)
        except Exception as e:
            raise Exception(f"网络请求异常：{e}")

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
        try:
            response = requests.post(url=url, json=data, params=querystring, timeout=10).json()
            if response.get("data"):
                return True, response["data"]["sign_daily_reward"]
            else:
                return False, response.get("message", "未知错误")
        except Exception as e:
            raise Exception(f"签到请求异常：{e}")

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


# ================== 主流程入口 ==================
def main():
    start_time = time.time()
    beijing_time = datetime.utcnow() + timedelta(hours=8)
    start_str = beijing_time.strftime("%Y-%m-%d %H:%M:%S")

    msg = f"🕓 执行时间（北京时间）：{start_str}\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

    cookie_quark = get_env()
    print(f"✅ 检测到 {len(cookie_quark)} 个夸克账号\n")

    for i, cookie in enumerate(cookie_quark):
        user_data = {}
        for a in cookie.replace(" ", "").split(';'):
            if not a == '':
                k, v = a.split('=', 1)
                user_data[k] = v

        try:
            log = Quark(user_data).do_sign()
            msg += f"🙍🏻‍♂️ 第{i + 1}个账号\n{log}\n"
        except Exception as e:
            err_msg = f"❌ 第{i + 1}个账号执行异常：{e}\n{traceback.format_exc()}"
            send("夸克签到失败 ❌", err_msg, success=False)
            raise  # 让 Action 识别为失败

    elapsed = round(time.time() - start_time, 2)
    msg += f"⏱️ 总耗时：{elapsed} 秒\n"

    send('夸克自动签到成功 ✅', msg)


if __name__ == "__main__":
    print("----------夸克网盘开始签到----------")
    try:
        main()
        print("----------夸克网盘签到完毕----------")
    except Exception as e:
        print(f"❌ 脚本运行失败: {e}")
        sys.exit(1)
