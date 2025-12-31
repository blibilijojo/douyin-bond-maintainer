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

        print('等待弹窗1')
        # 询问是否保存登陆信息 关闭
        try:
            page.get_by_text("取消").click(timeout=100000)
            print('点击私信按钮')
            page.get_by_role("paragraph").filter(has_text="私信").click()
        except TimeoutError:
            print('点击私信按钮')
            page.get_by_role("paragraph").filter(has_text="私信").click()
        
        # 循环处理多个用户
        for nickname in config['nicknames']:
            print(f'\n开始处理用户：{nickname}')
            print('点击续火花用户')
            page.get_by_text(f"{nickname}",exact=True).first.click()
            print('输入文本并回车')
            page.locator("#douyin-header-menuCt").get_by_role("textbox").locator("div").nth(2).click()
            page.locator("#douyin-header-menuCt").get_by_role("textbox").fill(f"{config['msg']}")
            page.locator("#douyin-header-menuCt").get_by_role("textbox").press("Enter")

            try:
                page.locator("text=发送失败").wait_for(timeout=10000)
                print(f'给 {nickname} 发送失败！')
                raise RuntimeError(f'给 {nickname} 发送失败!')
            except TimeoutError as e:
                print(f'给 {nickname} 发送成功！')
            
            # 返回到私信列表页
            page.get_by_role("button").filter(has_text="返回").click()

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
