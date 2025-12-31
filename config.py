import os
import json

def get_config():
    with open('cookies.json','r') as f:
        cookies = f.read()
        # print(cookies)
    nickname = os.getenv("NICKNAME")
    msg = os.getenv("MSG","火花")
    proxy = os.getenv("PROXY")
    
    # 新增配置项
    use_hitokoto = os.getenv("USE_HITOKOTO", "true").lower() == "true"
    use_txtapi = os.getenv("USE_TXTAPI", "true").lower() == "true"
    txtapi_url = os.getenv("TXTAPI_URL", "https://v1.hitokoto.cn/?encode=text")
    custom_template = os.getenv("CUSTOM_TEMPLATE", None)
    
    if proxy == '':
        proxy = None

    if cookies == '' or nickname == '':
        raise ValueError("SECRETS 未正确配置！")
    
    # 支持多用户，使用逗号分隔昵称
    nicknames = [name.strip() for name in nickname.split(',')] if nickname else []

    return {
        'cookies' : cookies,
        'nicknames' : nicknames,
        'msg' : msg,
        'proxy' : proxy,
        'use_hitokoto' : use_hitokoto,
        'use_txtapi' : use_txtapi,
        'txtapi_url' : txtapi_url,
        'custom_template' : custom_template
    }