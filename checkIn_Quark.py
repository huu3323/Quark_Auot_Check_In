import os
import re
import sys
import requests

# ✅ Telegram 推送函数（支持异常报警）
def send(title, message):
    print(f"{title}:\n{message}")

    tg_token = os.getenv("TG_BOT_TOKEN")
    tg_chat_id = os.getenv("TG_CHAT_ID")

    if tg_token and tg_chat_id:
        try:
            api_url = f"https://api.telegram.org/bot{tg_token}/sendMessage"
            payload = {
                "chat_id": tg_chat_id,
                "text": f"📢 {title}\n\n{message}",
                "parse_mode": "Markdown"
            }
            response = requests.post(api_url, data=payload)
            if response.status_code == 200:
                print("✅ Telegram 推送成功")
            else:
                print(f"❌ Telegram 推送失败: {response.text}")
        except Exception as e:
            print(f"❌ Telegram 推送异常: {e}")

# ✅ 读取环境变量
def get_env():
    if "COOKIE_QUARK" in os.environ:
        return re.split(r'\n|&&', os.environ.get("COOKIE_QUARK"))
    else:
        msg = "❌ 未设置 COOKIE_QUARK 环境变量"
        print(msg)
        send("夸克自动签到", msg)
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
        params = {
            "pr": "ucpro",
            "fr": "android",
            "kps": self.param.get("kps"),
            "sign": self.param.get("sign"),
            "vcode": self.param.get("vcode")
        }
        response = requests.get(url, params=params).json()
        return response.get("data", False)

    def get_growth_sign(self):
        url = "https://drive-m.quark.cn/1/clouddrive/capacity/growth/sign"
        params = {
            "pr": "ucpro",
            "fr": "android",
            "kps": self.param.get("kps"),
            "sign": self.param.get("sign"),
            "vcode": self.param.get("vcode")
        }
        data = {"sign_cyclic": True}
        response = requests.post(url, json=data, params=params).json()
        if response.get("data"):
            return True, response["data"]["sign_daily_reward"]
        else:
            return False, response.get("message", "未知错误")

    def do_sign(self):
        log = ""
        info = self.get_growth_info()
        if not info:
            raise Exception("Cookie 已失效或参数错误")

        username = self.param.get("user", "未知用户")
        user_type = "88VIP" if info.get("88VIP") else "普通用户"
        total_capacity = self.convert_bytes(info["total_capacity"])
        sign_total = self.convert_bytes(info["cap_composition"].get("sign_reward", 0))

        log += f"🙍🏻‍♂️ 用户: {username} ({user_type})\n"
        log += f"💾 网盘总容量: {total_capacity}，签到累计容量: {sign_total}\n"

        cap_sign = info["cap_sign"]
        if cap_sign["sign_daily"]:
            reward = self.convert_bytes(cap_sign["sign_daily_reward"])
            progress = f"({cap_sign['sign_progress']}/{cap_sign['sign_target']})"
            log += f"✅ 今日已签到: +{reward}\n连签进度: {progress}\n"
        else:
            success, result = self.get_growth_sign()
            if success:
                reward = self.convert_bytes(result)
                progress = f"({cap_sign['sign_progress'] + 1}/{cap_sign['sign_target']})"
                log += f"✅ 今日签到成功: +{reward}\n连签进度: {progress}\n"
            else:
                log += f"❌ 签到失败: {result}\n"

        return log

# ✅ 主程序，支持失败检测与标题变更
def main():
    msg = ""
    cookie_quark = get_env()
    has_error = False  # 是否有失败账号

    print(f"✅ 检测到共 {len(cookie_quark)} 个夸克账号\n")

    for i, cookie in enumerate(cookie_quark):
        user_data = {}
        for a in cookie.replace(" ", "").split(";"):
            if a:
                k, v = a.split("=", 1)
                user_data[k] = v

        msg += f"\n📌 账号 {i + 1}:\n"
        try:
            result = Quark(user_data).do_sign()
            msg += result
        except Exception as e:
            msg += f"❌ 签到失败: {str(e)}\n"
            has_error = True

    title = "夸克自动签到（部分失败）" if has_error else "夸克自动签到"
    send(title, msg.strip())

if __name__ == "__main__":
    print("----------夸克网盘开始签到----------")
    main()
    print("----------夸克网盘签到完毕----------")
    
