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
    username, password = env_variable.get('username'), env_variable.get('password')

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

    stakeAmt = 200
    default_timeout: int = 30 * 1000
    
    betking_tab = await context.new_page()
    if len(context.pages) > 1: await context.pages[0].close()

    betking_tab.set_default_navigation_timeout(default_timeout)
    betking_tab.set_default_timeout(default_timeout)

    balance_xpath: str = '//div[@class="user-balance-container"]'
    betking_virtual: str = 'https://m.betking.com/virtual/league/kings-league'
    Betking_mth_cntdown_xpath: str = '//span[@class="countdown-timer ng-star-inserted"]'
    live_mth_xpath: str = '//div[@class="live-badge ng-star-inserted" and contains(text(), "LIVE")]'
    betslip_xpath: str = '//span[@class="title ng-star-inserted" and contains(text(), "Betslip")]'
    login_success_popup_xpath: str = '//span[@class="toast-text" and contains(text(), "Login successful")]'
    
    async def log_in_betking():
        if betking_tab.url != betking_virtual:
            await betking_tab.goto(betking_virtual, wait_until="load")
            await expect(betking_tab.locator('//loading-spinner')).to_have_attribute("style", "display: none;")
        login_btn = betking_tab.get_by_role('button', name='LOGIN')
        not_logged_in = await login_btn.is_visible(timeout=1 * 1000)
        if not_logged_in:
            await login_btn.click()
            await expect(betking_tab.locator('//span[contains(text(), "Please Login")]')).to_be_visible(timeout=20 * 1000)
            await betking_tab.locator('//input[@formcontrolname="userName"]').fill(username)
            await betking_tab.locator('//input[@formcontrolname="password"]').fill(password)
            await betking_tab.get_by_role('button', name='LOGIN').nth(1).click()
            # Waits for Pop up to be visible 
            await expect(betking_tab.locator(login_success_popup_xpath)).to_be_visible(timeout=default_timeout)
            await expect(betking_tab.locator(balance_xpath)).to_be_visible(timeout=default_timeout)
            await betking_tab.get_by_test_id("o/u-2.5-market").click()
    
    async def get_team() -> list:
        hometeam: str = await realnaps_tab.inner_text('//div[@id="homeTxt" and @class="col"]')
        awayteam: str = await realnaps_tab.inner_text('//div[@id="awayTxt" and @class="col"]')
        return [hometeam, awayteam] 
    
    async def dot_position(position):
        if position == 0: return realnaps_tab.locator(f'//a[@class="swift bg-dark" and @name="{position}"]')
        return realnaps_tab.locator(f'//a[@class="swift" and @name="{position}"]')

    async def mth_timer() -> str:
        return await betking_tab.locator(Betking_mth_cntdown_xpath).inner_text()
    
    async def pred_day() -> int: 
        weekday: str = await realnaps_tab.inner_text('//span[@id="day"]')
        if weekday == '...':
            print("Waiting for preditions...")
            await expect(realnaps_tab.locator('//span[@id="day"]')
                        ).not_to_contain_text('...', timeout=default_timeout * 2)
            print(f"Prediction displayed.")
            return int(await realnaps_tab.inner_text('//span[@id="day"]'))
        return int(weekday)
    
    async def place_bet(): 
        await betking_tab.get_by_test_id('coupon-totals-stake-reset').click()
        await betking_tab.get_by_test_id('coupon-totals-stake-amount-value').fill(stakeAmt)
        await betking_tab.locator('//span[contains(text(), "Place Bet")]').click()
        await expect(betking_tab.locator('//span[contains(text(), "Best of luck!")]')).to_be_visible(timeout=default_timeout)
        await betking_tab.locator('//span[contains(text(), "CONTINUE BETTING")]').click()
        print("Bet Placed.")
    
    async def select_team_slide():
        # Randomly select 1 of 3 slides every season 
        current_season_dot_pos: int = randint(0, 2)  # 0=1, 1=2, 2=3
        team_slide = await dot_position(current_season_dot_pos) 
        await team_slide.click()
        print(f"We are working with team {current_season_dot_pos + 1} this season.")

    weekday = await pred_day()
    

    await log_in_betking()
    
    # Opens Realnaps
    realnaps_tab = await context.new_page()
    await realnaps_tab.goto("https://realnaps.com/signal/premium/ultra/Betking-england-league.php", wait_until="commit")

    match_is_live: bool = await betking_tab.locator(live_mth_xpath).is_visible(timeout=0)
    if match_is_live:
        expect(betking_tab.locator(live_mth_xpath)).not_to_be_visible(timeout=default_timeout * 2)



        

    # SEASON GAMES
    while True:
        # await select_team_slide()

        # WEEKDAY GAMES
        while True:
            # Get predicted team
            # await realnaps_tab.bring_to_front()
            if weekday != await pred_day(): continue
            
            team: list = await get_team()
            match_info: str = f"{'-'*10}Week {str(weekday)}{'-'*10}\nTeam: {team[0]} vs. {team[1]}"
            print(match_info)
            
    
async def main():
    async with async_playwright() as playwright:
        await run(playwright)

asyncio.run(main())
