import json
import requests

def parse_to_playwright_cookies(cookies):
    # 处理 Cookies 代码来自 ChatGPT
    same_site_map = {
        "no_restriction": "None",
        "lax": "Lax",
        "strict": "Strict",
        "unspecified": "Lax"
    }

    # 用列表推导式转换格式
    converted = [
        {
            "name": c["name"],
            "value": c["value"],
            "domain": c["domain"],
            "path": c.get("path", "/"),
            "secure": c.get("secure", False),
            "httpOnly": c.get("httpOnly", False),
            "expires": int(c["expirationDate"]) if "expirationDate" in c else -1,
            "sameSite": same_site_map.get(
                c.get("sameSite", "").lower() if isinstance(c.get("sameSite"), str) else "unspecified",
                "Lax"
            )
        }
        for c in json.loads(cookies)
    ]

    return converted

# 获取一言API内容
def get_hitokoto():
    try:
        response = requests.get("https://v1.hitokoto.cn/?c=a&c=b&c=c&c=d&c=e&c=f", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get("hitokoto", "") + "\n—— " + data.get("from", "")
    except Exception as e:
        print(f"获取一言API失败: {e}")
    return ""

# 获取TXTAPI内容
def get_txtapi_content(url="https://v1.hitokoto.cn/?encode=text", timeout=5):
    try:
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            return response.text.strip()
    except Exception as e:
        print(f"获取TXTAPI失败: {e}")
    return ""

# 生成续火消息
def generate_fire_message(base_msg="火花", use_hitokoto=True, use_txtapi=True, txtapi_url=None, custom_template=None):
    if custom_template:
        # 处理自定义模板
        message = custom_template
        if use_hitokoto:
            hitokoto = get_hitokoto()
            message = message.replace("[API]", hitokoto)
        if use_txtapi and txtapi_url:
            txtapi_content = get_txtapi_content(txtapi_url)
            message = message.replace("[TXTAPI]", txtapi_content)
        return message
    else:
        # 默认消息格式
        message = base_msg
        if use_hitokoto:
            hitokoto = get_hitokoto()
            if hitokoto:
                message += f"\n\n{hitokoto}"
        if use_txtapi and txtapi_url:
            txtapi_content = get_txtapi_content(txtapi_url)
            if txtapi_content:
                message += f"\n\n{txtapi_content}"
        return message