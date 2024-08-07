from playwright.async_api import async_playwright, Playwright, expect
from datetime import datetime, timedelta
from os import environ as env_variable
import asyncio, os, contextlib
from dotenv import load_dotenv
from random import randint

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

    stakeAmt = 200  # GOTO cal_nxt_mth_amt() and set ypur desired Amt
    default_timeout: int = 30 * 1000
    
    betking_tab = await context.new_page()
    if len(context.pages) > 1: await context.pages[0].close()

    betking_tab.set_default_navigation_timeout(default_timeout)
    betking_tab.set_default_timeout(default_timeout)

    balance_xpath: str = '//div[@class="user-balance-container"]'
    live_mths_container: str = '//div[@class="matches ng-star-inserted"]'
    live_clock_xpath: str = '//span[@class="live-icon ng-star-inserted"]'
    upcoming_week_xpath: str = '//div[@class="week ng-star-inserted active"]'
    betking_virtual_link: str = 'https://m.betking.com/virtual/league/kings-league'
    live_timer_FT_xpath: str = '//span[@class="timer" and contains(text(), "FT")]'
    rem_odds_xpath: str = '/../following-sibling::mvs-match-odds//div[@class="odds"]'
    Betking_mth_cntdown_xpath: str = '//span[@class="countdown-timer ng-star-inserted"]'
    live_checker_xpath: str = '//div[@class="selected league cat-league ng-star-inserted"]'
    realnaps_betking: str = "https://realnaps.com/signal/premium/ultra/betking-kings-league.php"
    login_form_xpath: str = '//span[@class="ng-tns-c210-2" and contains(text(), "Please Login")]'
    betslip_xpath: str = '//span[@class="title ng-star-inserted" and contains(text(), "Betslip")]'
    all_weeks_container_xpath: str = '//div[@class="week-container ng-star-inserted"]//child::div' 
    live_mth_xpath: str = '//div[@class="live-badge ng-star-inserted" and contains(text(), "LIVE")]'
    live_dot_xpath: str = live_checker_xpath+'//div[contains(text(), "LIVE")]//span[@class="inner-circle"]'
    login_success_popup_xpath: str = '//span[@class="toast-text" and contains(text(), "Login successful")]'
    
    async def log_in_betking():
        await betking_tab.goto(betking_virtual_link, wait_until="load", timeout=default_timeout * 2)
        await expect(betking_tab.locator('//loading-spinner')).to_have_attribute("style", "display: none;")
        login_btn = betking_tab.get_by_role('button', name='LOGIN')
        not_logged_in = await login_btn.is_visible(timeout=1 * 1000)
        if not_logged_in:
            await login_btn.click()
            await expect(betking_tab.locator(login_form_xpath)).to_be_visible(timeout=20 * 1000)
            await betking_tab.locator('//input[@formcontrolname="userName"]').fill(username)
            await betking_tab.locator('//input[@formcontrolname="password"]').fill(password)
            await betking_tab.get_by_role('button', name='LOGIN').nth(1).click()
            # Waits for Pop up to be visible 
            await expect(betking_tab.locator(login_success_popup_xpath)).to_be_visible(timeout=default_timeout)
            await expect(betking_tab.locator(balance_xpath)).to_be_visible(timeout=default_timeout)
            print("Successfully logged in.")
        else: print("Already logged in.")
        await betking_tab.get_by_test_id("o/u-2.5-market").click()
    
    async def get_team() -> list:
        hometeam: str = await realnaps_tab.inner_text('//div[@id="homeTxt" and @class="col"]')
        awayteam: str = await realnaps_tab.inner_text('//div[@id="awayTxt" and @class="col"]')
        return [hometeam, awayteam] 
    
    async def dot_position(position):
        if position == 0: return realnaps_tab.locator(f'//a[@class="swift bg-dark" and @name="{position}"]')
        return realnaps_tab.locator(f'//a[@class="swift" and @name="{position}"]')

    async def mth_timer() -> str:
        betking_tab.set_default_timeout(0)
        timer: str = await betking_tab.locator(Betking_mth_cntdown_xpath).inner_text()
        betking_tab.set_default_timeout(default_timeout)
        return timer.strip()
    
    async def pred_day() -> int: 
        weekday_rn: str = await realnaps_tab.inner_text('//span[@id="day"]')
        if weekday_rn == '...':
            await expect(realnaps_tab.locator('//span[@id="day"]')
                        ).not_to_contain_text('...', timeout=default_timeout * 2)
            # print(f"Prediction displayed.")
            return int(await realnaps_tab.inner_text('//span[@id="day"]'))
        
        return int(weekday_rn)
    
    async def place_bet(stakeAmt): 
        await betking_tab.locator(f'//div[contains(text(), "{team[0]}")]{rem_odds_xpath}').nth(0).click()
        await betking_tab.locator(betslip_xpath).click()
        await betking_tab.get_by_test_id('coupon-totals-stake-reset').click()
        await betking_tab.get_by_test_id('coupon-totals-stake-amount-value').fill(str(stakeAmt))
        await betking_tab.locator('//span[contains(text(), "Place Bet")]').click()
        with contextlib.suppress(AssertionError):
            await expect(betking_tab.locator(login_form_xpath)).to_be_visible(timeout=5 * 1000)
            print("Logged out already. Logging in...")
            await betking_tab.locator('//input[@formcontrolname="userName"]').fill(username)
            await betking_tab.locator('//input[@formcontrolname="password"]').fill(password)
            await betking_tab.get_by_role('button', name='LOGIN').nth(1).click()
            # Waits for Pop up to be visible 
            await expect(betking_tab.locator(login_success_popup_xpath)).to_be_attached(timeout=default_timeout)
            await expect(betking_tab.locator(balance_xpath)).to_be_attached(timeout=default_timeout)
            print("Successfully logged in.")
            await betking_tab.locator('//span[contains(text(), "Place Bet")]').click()
        await expect(betking_tab.locator('//span[contains(text(), "Best of luck!")]')).to_be_attached(timeout=default_timeout)
        await betking_tab.locator('//span[contains(text(), "CONTINUE BETTING")]').click()
        print(f"Bet Placed. Placed Amount= {stakeAmt}")
    
    async def select_team_slide():
        # Randomly select 1 of 3 slides every season 
        current_season_dot_pos: int = randint(0, 2)  # 0=1, 1=2, 2=3
        team_slide = await dot_position(current_season_dot_pos) 
        await team_slide.click()
        print(f"We are working with team {current_season_dot_pos + 1} this season.")

    async def match_is_live(weekday) -> list[bool, int] :
        match_live: bool = await betking_tab.locator(live_mth_xpath).is_visible(timeout=0)
        if match_live:
            live_mth_week: str = await betking_tab.locator(all_weeks_container_xpath).nth(0).inner_text()
            print(f"{live_mth_week} is live already.\nWaiting for match to end...")
            await expect(
                betking_tab.locator(
                    live_mth_xpath)).not_to_be_visible(timeout=default_timeout * 3)  # Live match duration is 30 secs
            print("Waiting for new week prediction...")
            weekday = int(live_mth_week.split(' ')[1]) + 1
        return [match_live, weekday]

    async def bk_nxt_mth_week() -> int:
        return int(str(await betking_tab.locator(all_weeks_container_xpath).nth(0).inner_text()).split(' ')[1])
    
    async def balance_is_visible() -> bool : 
        bal_is_visible: bool = await betking_tab.locator('//div[@class="user-balance-container"]').is_visible()
        if not bal_is_visible: await log_in_betking()
    
    async def cal_nxt_mth_amt() -> int:
        if lost_prev_match:
            return (losses + 100) / (round(float(odds[0]), 2) - 1)
        return 50
    
    await log_in_betking()

    # Opens Realnaps
    realnaps_tab = await context.new_page()
    await realnaps_tab.goto(realnaps_betking, wait_until="commit")
    rn_weekday = await pred_day() 

    # Check if match is live
    live, rn_weekday = await match_is_live(rn_weekday)
    if not live: 
        if rn_weekday != await bk_nxt_mth_week(): 
            print(f"Old weekday {rn_weekday} prediction still displayed.\nWaiting for new prediction...")
            rn_weekday += 1

    losses: int = 0  # Default should be 0
    lost_prev_match = False  # Default should be False

    # SEASON GAMES
    while True:
        # await select_team_slide()

        # WEEKDAY GAMES
        weekday_iteration = 0
        while True:
            # Get predicted team
            # await realnaps_tab.bring_to_front()  # COMMENT THIS ON SERVER
        
            if weekday_iteration == 0: print("Waiting for predictions...")
            weekday_iteration += 1
            if rn_weekday != await pred_day(): continue
            print(f"Prediction displayed.")
            weekday_iteration = 0
            
            team: list = await get_team()
            match_info: str = f"{'-'*10}Week {str(rn_weekday)}{'-'*10}\nTeam: {team[0]} vs. {team[1]}"
            
            await betking_tab.bring_to_front()
            if betking_tab.url != betking_virtual_link: 
                print("Logged out! 😕 Logging in...")
                await log_in_betking()

            # FIRST CHECK: if live match is live
            live, rn_weekday = await match_is_live(rn_weekday)
            if live: continue
            mthTimer: datetime = datetime.strptime(await mth_timer(), "%M:%S").time()
            timeout: datetime = datetime.strptime("00:00", "%M:%S").time()
            rem_time: timedelta = timedelta(hours=mthTimer.hour, minutes=mthTimer.minute, seconds=mthTimer.second) - timedelta(
                hours=timeout.hour, minutes=timeout.minute, seconds=timeout.second)
            str_rem_time: str = str(rem_time)
            if rem_time.total_seconds() < 2:
                print(f"Too late to place Week {rn_weekday} bet.\nWaiting for new prediction...")
                rn_weekday += 1
                continue
            elif rn_weekday != await bk_nxt_mth_week():
                print(f"For some reason, Week {rn_weekday} match is past.\nWaiting for new prediction...")
                rn_weekday += 1
                continue
            # await realnaps_tab.close()  # COMMENT THIS ON SERVER
            print(match_info)

            # Should incase it not on o/u 2.5 tab, click again
            await betking_tab.get_by_test_id("o/u-2.5-market").click()
            table = betking_tab.locator(f'//div[@class="body"]').nth(1)
            odds: list = str(await table.locator(
                f'//div[contains(text(), "{team[0]}")]{rem_odds_xpath}').inner_text()).split('\n')
            if str_rem_time.split(":")[1] == "00":
                print(f'Weekday {str(rn_weekday)} odd: {odds[0]}\nCountdown time is {str_rem_time.split(":")[2]} seconds.')
            else:
                print(
                    f'Weekday {str(rn_weekday)} odd: {odds[0]}\nCountdown time is {str_rem_time.split(":")[1]}:{str_rem_time.split(":")[2]}')
            
            stakeAmt = await cal_nxt_mth_amt()
            await balance_is_visible()  # Refresh the page if not visible
            await place_bet(stakeAmt)  # Place bet
            
            print(f"Waiting for match to begin...")
            await expect(betking_tab.locator(live_checker_xpath+'//div[@class="pie"]')).not_to_be_attached(timeout=default_timeout * 6)
            print("Match started...")
            # Incase displayed live match is not on the staked match 
            live_mth = betking_tab.locator(live_mths_container+f'//span[contains(text(), "{team[0]}")]')
            await expect(live_mth).to_be_attached(timeout=default_timeout)
            await live_mth.scroll_into_view_if_needed()
            await live_mth.click()
            # Scroll up by 1000 pixels
            await betking_tab.mouse.wheel(0, -1000)
            await expect(live_mth).to_be_visible(timeout=default_timeout)

            while True:
                # Checking live result
                home_score = await betking_tab.locator('//div[@class="home"]//child::*').count()
                away_score = await betking_tab.locator('//div[@class="away"]//child::*').count()
                try:
                    await expect(betking_tab.locator(live_dot_xpath)).to_be_visible(timeout=1000) # IMMEDIATELY
                    if (home_score + away_score) > 2:
                        print(f"Match Week {str(rn_weekday)} WON!")
                        lost_prev_match = False
                        losses = 0
                        break
                    else: continue
                except AssertionError:
                    print(f"Match Week {str(rn_weekday)} LOST!")
                    lost_prev_match = True
                    losses += stakeAmt
                    break

            # await log_in_betking()  # Refresh the page if not visible
            await betking_tab.goto(betking_virtual_link, wait_until="load", timeout=default_timeout * 2)
            await expect(betking_tab.locator('//loading-spinner')).to_have_attribute("style", "display: none;")
            await betking_tab.get_by_test_id("o/u-2.5-market").click()
            
            # realnaps_tab = await context.new_page()  # COMMENT THIS ON SERVER
            # await realnaps_tab.goto(realnaps_betking, wait_until="commit")  # COMMENT THIS ON SERVER
            if rn_weekday != 33: rn_weekday += 1
            else: # STOP AT WEEKDAY 33 CUS OF LAW OF DIMINISING RETURN
                rn_weekday = 1
                print(f"WEEK 33 MEANS END OF SEASON FOR US.\nWAITING FOR NEW SEASON TO BEGIN...")
                await asyncio.sleep(60 * 15)
                print(f"\n{'-'*10}NEW SEASON BEGINS{'-'*10}\nWAITING FOR NEW SEASON PREDICTIONS")


    
async def main():
    async with async_playwright() as playwright:
        await run(playwright)

asyncio.run(main())
