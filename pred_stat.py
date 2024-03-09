from random import randint
from dotenv import load_dotenv
import asyncio, os, contextlib, ast
from os import environ as env_variable
from datetime import datetime, timedelta
from playwright._impl._errors import TimeoutError
from playwright.async_api import async_playwright, Playwright, expect

load_dotenv(override=True)
async def run(playwright: Playwright):
    profile: str = "Betking-VF-profile"
    current_working_dir: str = os.getcwd()
    user_data_path: str = os.path.join(current_working_dir, profile)

    context = await playwright['chromium'].launch_persistent_context(
        args = ['--touch-events=enabled', '--disable-dev-shm-usage', '--disable-blink-features=AutomationControlled', '--incognito'],
        user_data_dir = user_data_path, 
        headless = False,
        color_scheme ='dark',
        channel= "chrome",
        user_agent = 'Mozilla/5.0 (Linux; Android 14; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.57 Mobile Safari/537.36',
        viewport = {'width': 400, 'height': 590},
        device_scale_factor = 2.625,
    )

    realnaps_tab = context.pages[0]
    default_timeout: int = 30 * 1000
    realnaps_tab.set_default_navigation_timeout(default_timeout)
    realnaps_tab.set_default_timeout(default_timeout)
    
    realnaps_betking: str = "https://realnaps.com/signal/premium/ultra/betking-kings-league.php"

    # Opens Realnaps
    await realnaps_tab.goto(realnaps_betking, wait_until="commit")
    
    async def get_team() -> list:
        hometeam: str = await realnaps_tab.inner_text('//div[@id="homeTxt" and @class="col"]')
        awayteam: str = await realnaps_tab.inner_text('//div[@id="awayTxt" and @class="col"]')
        return [hometeam, awayteam] 
    
    async def click_dot_position(position):
        await realnaps_tab.locator(f'//a[contains(text(), "{str(position)}")]').click()

    async def pred_day() -> int: 
        weekday: str = await realnaps_tab.inner_text('//span[@id="day"]')
        if weekday == '...':
            print("Waiting for preditions...")
            await expect(realnaps_tab.locator('//span[@id="day"]')
                        ).not_to_contain_text('...', timeout=default_timeout * 2)
            print(f"Prediction displayed.")
            return int(await realnaps_tab.inner_text('//span[@id="day"]'))
        return int(weekday)
    
    teams: dict = {}
    while True:
        weekday: int = await pred_day()
        for slideno in range(3):
            await click_dot_position(slideno)
            teams[f"team{slideno+1}"] = await get_team()
            # await realnaps_tab.locator('')
            # if slideno == 0:
            #     team1: list = await get_team()
            # elif slideno == 1:
            #     await click_dot_position(slideno)
            #     team2: list = await get_team()
            # elif slideno == 2: 
            #     await click_dot_position(slideno)
            #     team3: list = await get_team()
            #     await click_dot_position(0)  # Go back to teamslide 1
        print(f"Weekday {str(weekday)}")
        for key, value in teams.items():
            print(f"{key}: {value[0]} vs {value[1]}")
        # await realnaps_tab.get_by_role('button', name='Previous Predictions').click()
        # # await expect(realnaps_tab.locator('//div[@id="prevHolder"]//table').nth(0)).to_be_visible(timeout=default_timeout)
        # await realnaps_tab.locator('//select[@id="season"]').select_option(label="Current Season")
        # await realnaps_tab.locator('//select[@id="pick"]').select_option(label="Over 2.5")
        # await expect(realnaps_tab.locator('//div[@id="prevHolder"]//table').nth(0)).to_be_visible(timeout=default_timeout)
        # # print(await realnaps_tab.locator(f'//td[contains(text(), "week * {str(weekday - 1)}")]').first.inner_text())
        # for i in range(3):
        #     print(await realnaps_tab.locator(
        #         f'//td[contains(text(), "week * {str(weekday - 1)}")]//parent::tr').nth(i).inner_text())
        #     # print('-'*20)
        # # await asyncio.sleep()



        input("End of code: ")
        break
    
    await context.close()

    
async def main():
    async with async_playwright() as playwright:
        await run(playwright)

asyncio.run(main())
