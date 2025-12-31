import sys
from time import time
import traceback
import json
from playwright.sync_api import sync_playwright, TimeoutError
from config import get_config
from utils import parse_to_playwright_cookies, generate_fire_message

# 使用Playwright获取API内容
def get_api_content(page, url, is_json=True):
    try:
        # 创建新页面用于API请求
        api_page = page.context.new_page()
        
        # 访问API URL
        api_page.goto(url, wait_until="networkidle")
        
        # 获取页面内容
        content = api_page.content()
        
        # 关闭API页面
        api_page.close()
        
        if is_json:
            # 解析JSON内容
            data = json.loads(content)
            return data
        else:
            # 返回纯文本内容
            return content.strip()
    except Exception as e:
        print(f'API请求失败: {e}')
        return None

# 获取一言API内容
def get_hitokoto_content(page):
    try:
        data = get_api_content(page, "https://v1.hitokoto.cn/?c=a&c=b&c=c&c=d&c=e&c=f")
        if data:
            return data.get("hitokoto", "") + "\n—— " + data.get("from", "")
    except Exception as e:
        print(f'获取一言API失败: {e}')
    return ""

# 获取TXTAPI内容
def get_txtapi_content(page, url):
    try:
        content = get_api_content(page, url, is_json=False)
        if content:
            return content
    except Exception as e:
        print(f'获取TXTAPI失败: {e}')
    return ""

print('开始执行...')
start_time = time()

with sync_playwright() as playwright:
    try:
        config = get_config()
        browser = playwright.chromium.launch(headless=True)
        
        # 只有当proxy不为None时才传递proxy参数
        context_options = {}
        if config['proxy']:
            context_options['proxy'] = {"server": config['proxy']}
        context = browser.new_context(**context_options)
        
        context.add_cookies(parse_to_playwright_cookies(config['cookies']))

        page = context.new_page()

        # 生成续火消息，先获取API内容
        hitokoto_content = ""
        txtapi_content = ""
        
        # 获取一言API内容
        if config['use_hitokoto']:
            print('正在获取一言API内容...')
            hitokoto_content = get_hitokoto_content(page)
        
        # 获取TXTAPI内容
        if config['use_txtapi'] and config['txtapi_url']:
            print('正在获取TXTAPI内容...')
            txtapi_content = get_txtapi_content(page, config['txtapi_url'])
        
        # 生成消息
        fire_message = generate_fire_message(
            base_msg=config['msg'],
            custom_template=config['custom_template'],
            hitokoto_content=hitokoto_content,
            txtapi_content=txtapi_content
        )
        print(f'生成的续火消息：{fire_message[:20]}...')  # 只显示前20个字符
        
        # 直接访问创作者平台聊天页面（根据油猴脚本的匹配URL）
        page.goto("https://creator.douyin.com/creator-micro/data/following/chat")

        # 等待页面加载完成
        page.wait_for_load_state("networkidle")
        
        print('页面加载完成，开始查找私信列表')
        
        # 等待私信列表加载
        try:
            # 等待聊天列表区域加载
            page.wait_for_selector("div", timeout=30000)  # 等待任意div元素加载
            print('页面元素加载成功')
        except TimeoutError:
            print('页面加载超时，尝试刷新页面')
            page.reload()
            page.wait_for_load_state("networkidle")
            page.wait_for_selector("div", timeout=30000)
        
        # 循环处理多个用户
        for nickname in config['nicknames']:
            print(f'\n开始处理用户：{nickname}')
            print('查找并点击续火花用户')
            
            # 使用多种方式查找用户
            user_locators = [
                # 1. 精确匹配用户名
                page.get_by_text(f"{nickname}", exact=True),
                # 2. 聊天列表中查找用户名
                page.locator(".chat-item").filter(has_text=f"{nickname}"),  # 替换为实际的class名
                # 3. 模糊匹配包含用户名的元素
                page.locator(f"//*[contains(text(), '{nickname}')]").first,
                # 4. 使用data属性定位
                page.locator(f"[data-nickname='{nickname}']"),
                # 5. 使用title属性定位
                page.locator(f"[title*='{nickname}']")
            ]
            
            user_found = False
            for locator in user_locators:
                try:
                    locator.click(timeout=15000)
                    user_found = True
                    print(f'找到并点击用户：{nickname}')
                    
                    # 等待聊天窗口加载
                    page.wait_for_selector(".chat-window", timeout=10000)  # 替换为实际的class名
                    print('聊天窗口加载成功')
                    break
                except Exception as e:
                    continue
            
            if not user_found:
                print(f'未找到用户：{nickname}，跳过该用户')
                continue
            
            print('查找输入框并发送消息')
            
            # 使用更通用的方式查找输入框
            input_locators = [
                # 1. 直接查找文本框
                page.get_by_role("textbox"),
                # 2. 查找textarea元素
                page.locator("textarea"),
                # 3. 根据placeholder查找
                page.locator("[placeholder*='发送消息']"),
                # 4. 根据class查找
                page.locator(".chat-input"),  # 替换为实际的class名
                # 5. 根据id查找
                page.locator("#chat-input")  # 替换为实际的id名
            ]
            
            input_found = False
            for locator in input_locators:
                try:
                    # 点击输入框
                    locator.click(timeout=5000)
                    # 清除现有内容（如果有）
                    locator.clear(timeout=5000)
                    # 输入消息
                    locator.fill(fire_message, timeout=5000)
                    # 发送消息
                    locator.press("Enter", timeout=5000)
                    input_found = True
                    print('消息发送成功')
                    break
                except Exception as e:
                    continue
            
            if not input_found:
                print(f'未找到输入框，无法给用户 {nickname} 发送消息')
                # 尝试返回私信列表
                try:
                    page.goto("https://creator.douyin.com/creator-micro/data/following/chat")
                    page.wait_for_load_state("networkidle")
                except Exception as e:
                    pass
                continue
            
            # 检查发送失败状态
            try:
                page.locator("text=发送失败").wait_for(timeout=10000)
                print(f'给 {nickname} 发送失败！')
            except TimeoutError as e:
                print(f'给 {nickname} 发送成功！')
            
            # 等待消息发送完成，然后继续下一个用户
            page.wait_for_timeout(2000)
        
        print("\n所有用户处理完成！")
        print(f"耗时：{int(time() - start_time)}秒")
        
        print('关闭浏览器')
        context.close()
        browser.close()
        
        print('执行完成！')
        
    except Exception as e:
        error_details = traceback.format_exc()
        print(f'发生错误：{error_details}')

        try:
            # 确保page对象存在时才尝试截图
            if 'page' in locals():
                screenshot = page.screenshot(path='error.png', full_page=True)
                print('错误截图已保存')
        except Exception as e:
            print(f'保存截图失败：{e}')

        sys.exit(1)
