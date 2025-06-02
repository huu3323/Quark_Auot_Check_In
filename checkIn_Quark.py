import os
import re
import sys
import requests

# Telegram 推送函数
def send(title, message):
    print(f"{title}:\n{message}")

    telegram_token = os.getenv("TG_BOT_TOKEN")
    telegram_chat_id = os.getenv("TG_CHAT_ID")

    if telegram_token and telegram_chat_id:
        try:
            telegram_api = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
            payload = {
                "chat_id": telegram_chat_id,
                "text": f"📢 {title}\n\n{message}",
                "parse_mode": "Markdown"
            }
            response = requests.post(telegram_api, data=payload)
            if response.status_code == 200:
                print("✅ Telegram 推送成功")
            else:
                print("❌ Telegram 推送失败", response.text)
        except Exception as e:
            print("❌ Telegram 推送异常:", str(e))


# 读取 cookie 环境变量
def get_env():
    if "COOKIE_QUARK" in os.environ:
        return re.split(r'\n|&&', os.environ.get('COOKIE_QUARK'))
    else:
        msg = '❌ 未添加 COOKIE_QUARK 环境变量'
        print(msg)
        send('夸克自动签到', msg)
        sys.exit(0)


class Quark:
    def __init__(self, user_data):
        self.param = user_data

    def convert_bytes(self, b):
        units = ("B", "KB", "MB", "GB", "TB", "PB")
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
        log = ""
        growth_info = self.get_growth_info()
        if not growth_info:
            raise Exception("❌ 获取成长信息失败，可能是 Cookie 已失效")

        username = self.param.get('user', '未知用户')
        user_type = '88VIP' if growth_info['88VIP'] else '普通用户'
        total = self.convert_bytes(growth_info['total_capacity'])
        sign_total = self.convert_bytes(growth_info['cap_composition'].get('sign_reward', 0))

        log += f"🙍🏻‍♂️ 用户: {username} ({user_type})\n"
        log += f"💾 网盘总容量: {total}，签到累计容量: {sign_total}\n"

        cap_sign = growth_info["cap_sign"]
        if cap_sign["sign_daily"]:
            reward = self.convert_bytes(cap_sign["sign_daily_reward"])
            progress = f"({cap_sign['sign_progress']}/{cap_sign['sign_target']})"
            log += f"✅ 今日已签到: +{reward}\n连签进度: {progress}\n"
        else:
            success, reward_or_msg = self.get_growth_sign()
            if success:
                reward = self.convert_bytes(reward_or_msg)
                progress = f"({cap_sign['sign_progress'] + 1}/{cap_sign['sign_target']})"
                log += f"✅ 今日签到成功: +{reward}\n连签进度: {progress}\n"
            else:
                log += f"❌ 签到失败: {reward_or_msg}\n"

        return log


def main():
    msg = ""
    cookie_quark = get_env()

    print(f"✅ 检测到共 {len(cookie_quark)} 个夸克账号\n")

    for i, cookie in enumerate(cookie_quark):
        user_data = {}
        for a in cookie.replace(" ", "").split(';'):
            if a:
                k, v = a.split('=', 1)
                user_data[k] = v

        msg += f"\n📌 账号 {i + 1}:\n"
        try:
            result = Quark(user_data).do_sign()
            msg += result
        except Exception as e:
            msg += f"❌ 账号 {i + 1} 异常: {str(e)}\n"

    send("夸克自动签到", msg.strip())


if __name__ == "__main__":
    print("----------夸克网盘开始签到----------")
    main()
    print("----------夸克网盘签到完毕----------")
    
