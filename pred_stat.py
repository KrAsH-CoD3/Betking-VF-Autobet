from random import randint
from dotenv import load_dotenv
import asyncio, os, contextlib, ast
from os import environ as env_variable
from datetime import datetime, timedelta
from playwright._impl._errors import TimeoutError
from playwright.async_api import async_playwright, Playwright, expect

load_dotenv(override=True)
async def run(playwright: Playwright):
    profile: str = "Betking-VF-result-profile"
    current_working_dir: str = os.getcwd()
    user_data_path: str = os.path.join(current_working_dir, profile)

    context = await playwright['chromium'].launch_persistent_context(
        args = ['--touch-events=enabled', '--disable-dev-shm-usage', '--disable-blink-features=AutomationControlled'],
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
    
    betking_virtual_result: str = 'https://m.betking.com/virtual/league/kings-league/results'
    realnaps_betking: str = "https://realnaps.com/signal/premium/ultra/betking-kings-league.php"

        
    async def get_team() -> list:
        hometeam: str = await realnaps_tab.inner_text('//div[@id="homeTxt" and @class="col"]')
        awayteam: str = await realnaps_tab.inner_text('//div[@id="awayTxt" and @class="col"]')
        return [hometeam, awayteam] 
    
    async def pred_day() -> int: 
        weekday: str = await realnaps_tab.inner_text('//span[@id="day"]')
        if weekday == '...':
            print("Waiting for preditions...")
            await expect(realnaps_tab.locator('//span[@id="day"]')
                        ).not_to_contain_text('...', timeout=default_timeout * 2)
            print(f"Prediction displayed.")
            return int(await realnaps_tab.inner_text('//span[@id="day"]'))
        return int(weekday)
    
    betking_tab = await context.new_page()
    await betking_tab.goto(betking_virtual_result, wait_until="commit")

    # Opens Realnaps
    await realnaps_tab.goto(realnaps_betking, wait_until="commit")
    with contextlib.suppress(TimeoutError): await realnaps_tab.locator('//p[contains(text(), "Consent")]').click(timeout=10 * 1000)

    season_teams: dict = {}
    teams: dict = {}
    iterate: int = 0
    while True:
        weekday: int = await pred_day()
        for slideno in range(3):
            if slideno != 0: 
                await realnaps_tab.locator(f'//a[contains(text(), "{slideno+1}")]').click()
            teams[f"team{slideno+1}"] = await get_team()
            if slideno == 2: # Click back to the first team 
                await realnaps_tab.locator(f'//a[contains(text(), "{1}")]').click()
        
        # Wait until next prediction is displayed so as get result
        while True: 
            new_weekday: int = await pred_day()
            if weekday == new_weekday: continue
            break
        # Reload to get match result
        await betking_tab.reload()
        print(f"{'-'*9}Weekday {weekday}{'-'*9}")
        match_table: str = f'//mvs-tournament-results//div[text()="Week {weekday}"]/../..'
        for key, value in teams.items(): 
            score_cell_xpath = f'//div[contains(text(), "{value[0]}")]/..//following-sibling::div[@class="score ft"]'
            match_score = await betking_tab.locator(match_table+score_cell_xpath).inner_text()
            home_score: int = int(match_score.split(" - ")[0])
            away_score: int = int(match_score.split(" - ")[1])
            teams[key] += [match_score, "WON!" if (home_score + away_score) > 2 else "LOST!"]
            print(f"{key}: {value[0]} vs {value[1]}: {match_score} {value[-1]}")
        iterate += 1
        # if iterate > 5:
        #     await asyncio.sleep(120 * 5)  # 3mins * 5 times(matches)
        #     iterate = 0

        # //div[@class="week-row"]/child::span
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



        # input("End of code: ")
        # break
    
    await context.close()

    
async def main():
    async with async_playwright() as playwright:
        await run(playwright)

asyncio.run(main())
