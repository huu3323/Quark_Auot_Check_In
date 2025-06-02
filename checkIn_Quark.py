import os
import re
import sys
import requests

cookie_list = os.getenv("COOKIE_QUARK").split('\n|&&')

# Telegram 推送
def telegram_send(token, chat_id, message):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"  # 用Markdown格式美化推送
    }
    try:
        resp = requests.post(url, data=payload)
        if resp.status_code == 200:
            print("✅ Telegram 推送成功")
        else:
            print(f"❌ Telegram 推送失败，状态码：{resp.status_code}，响应：{resp.text}")
    except Exception as e:
        print(f"❌ Telegram 推送异常: {e}")

# 替代 notify 功能，增加Telegram推送
def send(title, message):
    print(f"{title}: {message}")
    tg_token = os.getenv("TG_BOT_TOKEN")
    tg_chat_id = os.getenv("TG_CHAT_ID")
    if tg_token and tg_chat_id:
        telegram_send(tg_token, tg_chat_id, f"*{title}*\n\n{message}")
    else:
        print("⚠️ 未配置 Telegram Bot Token 或 Chat ID，跳过推送")

# 获取环境变量
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
        if response.get("data"):
            return response["data"]
        else:
            return False

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
        log = ""
        growth_info = self.get_growth_info()
        if growth_info:
            member_type = growth_info.get("member_type", "")
            if member_type == "SUPER_VIP":
                user_type = "SVIP"
            elif growth_info.get("88VIP"):
                user_type = "88VIP"
            else:
                user_type = "普通用户"

            user_name = self.param.get('user')
            total_capacity = growth_info.get("cap_growth", {}).get("cur_total_cap", 0)
            sign_reward_capacity = growth_info.get("cap_composition", {}).get("sign_reward", 0)

            log += f"📌 账号:\n"
            log += f"🙍🏻‍♂️ 用户: {user_name}\n"
            log += f"💾 网盘总容量: {self.convert_bytes(total_capacity)}，签到累计容量: {self.convert_bytes(sign_reward_capacity)}\n"

            cap_sign = growth_info.get("cap_sign", {})
            if cap_sign.get("sign_daily", False):
                log += f"✅ 今日签到成功: +{self.convert_bytes(cap_sign.get('sign_daily_reward', 0))}\n"
                log += f"连签进度: ({cap_sign.get('sign_progress', 0)}/{cap_sign.get('sign_target', 0)})\n"
            else:
                sign, sign_return = self.get_growth_sign()
                if sign:
                    progress = cap_sign.get('sign_progress', 0) + 1
                    target = cap_sign.get('sign_target', 0)
                    log += f"✅ 今日签到成功: +{self.convert_bytes(sign_return)}\n"
                    log += f"连签进度: ({progress}/{target})\n"
                else:
                    log += f"❌ 签到异常: {sign_return}\n"
        else:
            raise Exception("❌ 签到异常: 获取成长信息失败")
        return log


def main():
    msg = "📢 夸克自动签到\n\n"
    cookie_quark = get_env()

    print(f"✅ 检测到共 {len(cookie_quark)} 个夸克账号\n")

    for i, cookie in enumerate(cookie_quark, 1):
        user_data = {}
        for a in cookie.replace(" ", "").split(';'):
            if a != '':
                user_data.update({a[0:a.index('=')]: a[a.index('=') + 1:]})
        try:
            log = Quark(user_data).do_sign()
            # 加入账号序号
            msg += f"📌 账号 {i}:\n" + log + "\n"
        except Exception as e:
            err_msg = f"📌 账号 {i}:\n❌ 错误: {str(e)}\n"
            msg += err_msg
            print(err_msg)

    send('夸克自动签到', msg)
    return msg[:-1]


if __name__ == "__main__":
    print("----------夸克网盘开始签到----------")
    main()
    print("----------夸克网盘签到完毕----------")
