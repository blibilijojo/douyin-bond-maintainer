import sys
from time import  time
import traceback
from playwright.sync_api import sync_playwright , TimeoutError
from config import get_config
from utils import parse_to_playwright_cookies

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

        page.goto("https://www.douyin.com/?recommend=1")

        # 等待页面加载完成
        page.wait_for_load_state("networkidle")
        
        print('等待弹窗1')
        # 询问是否保存登陆信息 关闭
        try:
            page.get_by_text("取消").click(timeout=10000)
        except TimeoutError:
            print('没有找到保存登陆信息弹窗')
        
        print('查找并点击私信按钮')
        # 根据提供的HTML结构，使用更精确的选择器定位私信按钮
        private_chat_locators = [
            # 1. 直接点击包含"私信"文本的p标签
            page.get_by_text("私信"),
            # 2. 点击p标签的父元素div
            page.locator("p.jenVD1aU").filter(has_text="私信").locator(".."),
            # 3. 使用data-e2e属性定位
            page.locator("[data-e2e*='button']").filter(has_text="私信"),
            # 4. 使用完整的class定位
            page.locator(".vUlcfDbY.d5oQ4GPx.XuCIp3h8").filter(has_text="私信"),
            # 5. 使用XPath定位包含私信文本的div
            page.locator("//div[contains(., '私信')]").first
        ]
        
        private_chat_found = False
        for locator in private_chat_locators:
            try:
                locator.click(timeout=10000)
                private_chat_found = True
                print('私信按钮点击成功')
                break
            except Exception as e:
                continue
        
        if not private_chat_found:
            raise RuntimeError('未找到私信按钮，请检查页面结构是否变化')
        
        # 循环处理多个用户
        for nickname in config['nicknames']:
            print(f'\n开始处理用户：{nickname}')
            print('查找并点击续火花用户')
            
            # 使用多种方式查找用户
            user_locators = [
                page.get_by_text(f"{nickname}", exact=True).first,
                page.locator(f"[title*='{nickname}']").first,
                page.locator(f"//*[contains(text(), '{nickname}')]").first,
                page.locator(f"[data-nickname='{nickname}']").first
            ]
            
            user_found = False
            for locator in user_locators:
                try:
                    locator.click(timeout=10000)
                    user_found = True
                    print(f'找到并点击用户：{nickname}')
                    break
                except Exception as e:
                    continue
            
            if not user_found:
                print(f'未找到用户：{nickname}，跳过该用户')
                continue
            
            print('输入文本并回车')
            
            # 使用更通用的方式查找输入框
            input_locators = [
                page.get_by_role("textbox"),
                page.locator("textarea"),
                page.locator("[placeholder*='发送消息']"),
                page.locator("[id*='input']").locator("[type='text']")
            ]
            
            input_found = False
            for locator in input_locators:
                try:
                    locator.click(timeout=5000)
                    locator.fill(f"{config['msg']}")
                    locator.press("Enter")
                    input_found = True
                    print('消息发送成功')
                    break
                except Exception as e:
                    continue
            
            if not input_found:
                print(f'未找到输入框，无法给用户 {nickname} 发送消息')
                # 尝试返回私信列表
                try:
                    page.goto("https://www.douyin.com/message")
                    page.wait_for_load_state("networkidle")
                except Exception as e:
                    pass
                continue
            
            try:
                page.locator("text=发送失败").wait_for(timeout=10000)
                print(f'给 {nickname} 发送失败！')
            except TimeoutError as e:
                print(f'给 {nickname} 发送成功！')
            
            # 返回到私信列表页
            print('返回私信列表页')
            back_button_locators = [
                page.get_by_text("返回"),
                page.get_by_role("button").filter(has_text="返回"),
                page.locator("[aria-label*='返回']"),
                page.locator("[title*='返回']"),
                page.locator("//*[contains(text(), '返回')]").first
            ]
            
            back_button_found = False
            for locator in back_button_locators:
                try:
                    locator.click(timeout=5000)
                    back_button_found = True
                    print('返回按钮点击成功')
                    break
                except Exception as e:
                    continue
            
            if not back_button_found:
                print('未找到返回按钮，尝试刷新页面回到私信列表')
                page.goto("https://www.douyin.com/message")
                page.wait_for_load_state("networkidle")

        print("\n所有用户处理完成！")
        print("耗时："+str(int(time() - start_time)))
        # sleep(10)

        print('关闭浏览器')

        context.close()
        browser.close()
    except Exception as e:
    # error_msg = str(e)
        error_details = traceback.format_exc()
        print(error_details)

        try :
            # 确保page对象存在时才尝试截图
            if 'page' in locals():
                screenshot = page.screenshot(path='error.png',full_page=True)
        except Exception as e:
            print(e)

        sys.exit(1)
