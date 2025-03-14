import os
import re
import sys
import requests

# 替代 notify 功能，支持 Telegram 推送
def send(title, message):
    print(f"{title}: {message}")

    # 你的 Telegram Bot Token 和 Chat ID（从环境变量读取）
    BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
    CHAT_ID = os.getenv("TG_CHAT_ID")

    if BOT_TOKEN and CHAT_ID:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": f"📢 {title}\n\n{message}"}
        try:
            response = requests.post(url, json=data)
            if response.status_code == 200:
                print("✅ Telegram 消息发送成功！")
            else:
                print("❌ Telegram 消息发送失败！", response.text)
        except Exception as e:
            print("❌ Telegram 发送异常:", str(e))
    else:
        print("❌ 未设置 Telegram 相关环境变量")

# 获取环境变量
def get_env():
    if "COOKIE_QUARK" in os.environ:
        return re.split(r'\n|&&', os.environ.get('COOKIE_QUARK'))
    else:
        print('❌ 未添加 COOKIE_QUARK 变量')
        send('夸克自动签到', '❌ 未添加 COOKIE_QUARK 变量')
        sys.exit(0)

class Quark:
    '''Quark 类封装签到、领取签到奖励的方法'''

    def __init__(self, user_data):
        self.param = user_data

    def convert_bytes(self, b):
        '''字节转换为 MB、GB、TB'''
        units = ("B", "KB", "MB", "GB", "TB", "PB")
        i = 0
        while b >= 1024 and i < len(units) - 1:
            b /= 1024
            i += 1
        return f"{b:.2f} {units[i]}"

    def get_growth_info(self):
        '''获取用户当前的签到信息'''
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
        '''执行签到请求'''
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
            return False, response.get("message", "签到失败")

    def do_sign(self):
        '''执行签到任务'''
        log = ""
        growth_info = self.get_growth_info()
        if growth_info:
            log += (
                f" {'88VIP' if growth_info['88VIP'] else '普通用户'} {self.param.get('user')}\n"
                f"💾 网盘总容量：{self.convert_bytes(growth_info['total_capacity'])}，"
                f"签到累计容量：{self.convert_bytes(growth_info.get('cap_composition', {}).get('sign_reward', 0))}\n"
            )

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
    '''主函数'''
    msg = ""
    cookie_quark = get_env()

    print(f"✅ 检测到共 {len(cookie_quark)} 个夸克账号\n")

    for i, cookie in enumerate(cookie_quark):
        user_data = {}
        for a in cookie.replace(" ", "").split(';'):
            if '=' in a:
                key, value = a.split('=', 1)
                user_data[key] = value

        log = f"🙍🏻‍♂️ 第 {i + 1} 个账号\n"
        msg += log
        log = Quark(user_data).do_sign()
        msg += log + "\n"

    # 发送 Telegram 通知
    send('夸克自动签到', msg.strip())

if __name__ == "__main__":
    print("----------夸克网盘开始签到----------")
    main()
    print("----------夸克网盘签到完毕----------")
