import json

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

# 生成续火消息，不包含网络请求（移到main.py中处理）
def generate_fire_message(base_msg="火花", custom_template=None, hitokoto_content="", txtapi_content=""):
    if custom_template:
        # 处理自定义模板
        message = custom_template
        message = message.replace("[API]", hitokoto_content)
        message = message.replace("[TXTAPI]", txtapi_content)
        return message
    else:
        # 默认消息格式
        message = base_msg
        if hitokoto_content:
            message += f"\n\n{hitokoto_content}"
        if txtapi_content:
            message += f"\n\n{txtapi_content}"
        return message