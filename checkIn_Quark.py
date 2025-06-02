import os
import re
import sys
import requests

# 替代 notify 功能，加入 Telegram 推送
def send(title, message):
    print(f"{title}: {message}")

    # Telegram 推送
    telegram_token = os.getenv("TG_BOT_TOKEN")
    telegram_chat_id = os.getenv("TG_CHAT_ID")

    if telegram_token and telegram_chat_id:
        try:
            telegram_api = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
            payload = {
                "chat_id": telegram_chat_id,
                "text": f"{title}\n{message}",
                "parse_mode": "Markdown"
            }
            response = requests.post(telegram_api, data=payload)
            if response.status_code == 200:
                print("✅ Telegram 推送成功")
            else:
                print("❌ Telegram 推送失败", response.text)
        except Exception as e:
            print("❌ Telegram 推送异常:", str(e))

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
            return False, response["message"]

    def queryBalance(self):
        url = "https://coral2.quark.cn/currency/v1/queryBalance"
        querystring = {
            "moduleCode": "1f3563d38896438db994f118d4ff53cb",
            "kps": self.param.get('kps'),
        }
        response = requests.get(url=url, params=querystring).json()
        if response.get("data"):
            return response["data"]["balance"]
        else:
            return response["msg"]

    def do_sign(self):
        log = ""
        growth_info = self.get_growth_info()
        if growth_info:
            log += (
                f" {'88VIP' if growth_info['88VIP'] else '普通用户'} {self.param.get('user')}\n"
                f"💾 网盘总容量：{self.convert_bytes(growth_info['total_capacity'])}，"
                f"签到累计容量：")
            if "sign_reward" in growth_info['cap_composition']:
                log += f"{self.convert_bytes(growth_info['cap_composition']['sign_reward'])}\n"
            else:
                log += "0 MB\n"
            if growth_info["cap_sign"]["sign_daily"]:
                log += (
                    f"✅ 签到日志: 今日已签到+{self.convert_bytes(growth_info['cap_sign']['sign_daily_reward'])}，"
                    f"连签进度({growth_info['cap_sign']['sign_progress']}/{growth_info['cap_sign']['sign_target']})\n"
                )
            else:
                sign, sign_return = self.get_growth_sign()
                if sign:
                    log += (
                        f"✅ 执行签到: 今日签到+{self.convert_bytes(sign_return)}，"
                        f"连签进度({growth_info['cap_sign']['sign_progress'] + 1}/{growth_info['cap_sign']['sign_target']})\n"
                    )
                else:
                    log += f"❌ 签到异常: {sign_return}\n"
        else:
            raise Exception("❌ 签到异常: 获取成长信息失败")

        return log

def main():
    msg = ""
    cookie_quark = get_env()

    print("✅ 检测到共", len(cookie_quark), "个夸克账号\n")

    for i, cookie in enumerate(cookie_quark):
        user_data = {}
        for a in cookie.replace(" ", "").split(';'):
            if a:
                user_data.update({a.split('=')[0]: a.split('=')[1]})
        log = f"🙍🏻‍♂️ 第{i + 1}个账号\n"
        msg += log
        try:
            log = Quark(user_data).do_sign()
            msg += log + "\n"
        except Exception as e:
            msg += f"❌ 第{i + 1}个账号出错: {str(e)}\n"

    try:
        send('夸克自动签到', msg.strip())
    except Exception as err:
        print('%s\n❌ 推送失败，请查看日志' % err)

    return msg.strip()

if __name__ == "__main__":
    print("----------夸克网盘开始签到----------")
    main()
    print("----------夸克网盘签到完毕----------")
    
