from multiprocessing import pool
import os
import re
import asyncio
import pandas as pd
import psycopg
import psycopg_pool
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import httpx
import curl_cffi
from curl_cffi import AsyncSession

connect = "dbname=jobdata user=postgres password=1234 host=localhost port=5432"

async def scraping_urls():
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir="./user_data",
            channel="chrome",
            headless=False,
            # This argument helps bypass some automation detections
            args=["--disable-blink-features=AutomationControlled"]
        )
        page = await browser.new_page()
        
        await page.goto("https://www.pracuj.pl/")
        cookie = page.locator("[data-test=\"button-submitCookie\"]")
        if await cookie.is_visible():
            await cookie.click()
        reklama = page.get_by_label("Szukasz pracownika?").get_by_role("button").filter(has_text=re.compile(r"^$"))
        if await reklama.is_visible():
            await reklama.click()
        await page.locator("[data-test=\"input-kw\"] [data-test=\"input-field\"]").click()
        await page.locator("[data-test=\"input-kw\"] [data-test=\"input-field\"]").fill("Data analyst")
        await page.locator("[data-test=\"input-kw\"] [data-test=\"input-field\"]").press("Enter")
        # page.locator("iframe[src=\"https://challenges.cloudflare.com/cdn-cgi/challenge-platform/h/b/turnstile/f/ov2/av0/rch/h0z7a/0x4AAAAAAADnPIDROrmt1Wwj/light/fbE/new/normal?lang=auto\"]").content_frame.locator("body").click()
        
        parsed = []
        url_set = set()
        page_number = 1
        
        while True:
            # this worked, but on website there are 3 buttons, so playwright wrote in console code for them
            # next_button = page.get_by_role("button", name="Następna")
            next_button = page.locator('[data-test="top-pagination-next-button"]')
            
            await page.wait_for_load_state("networkidle")
            print("Processing page:", page_number)
            soup = BeautifulSoup(await page.content(), features="html.parser")
            
            for url in soup.find_all(attrs={"data-test": "link-offer"}):
                # find() returns None if not found, so we check before accessing attributes
                
                text_of_url = url.get("href") if url else "None"
                if text_of_url != "None" and text_of_url not in url_set:
                    url_set.add(text_of_url)
                    parsed.append({
                        'job url': text_of_url,
                    })
            if await next_button.is_visible():
                await next_button.click()
                page_number += 1
                await page.wait_for_load_state("load")
            else:
                break
        await browser.close()
        
        if not parsed:
            print("No URLs found.")
            return
        
        df_new = pd.DataFrame(parsed, columns=['job url'])
        csv_filename = 'url.csv'
        if os.path.exists(csv_filename):
            try:
                df_existing = pd.read_csv(csv_filename)
                if 'job url' in df_existing.columns:
                    df_new = df_new[~df_new['job url'].isin(df_existing['job url'])]
            except pd.errors.EmptyDataError:
                print("Error with reading CSV")
            if not df_new.empty:
                df_new.to_csv(csv_filename, mode='a', index=False, header=False)
            else:
                print("All links are already in the file")
        else:
            df_new.to_csv(csv_filename, mode='w', index=False, header=True)
            
        
async def scrap_one_page(url, session):
    # page = await browser.new_page()
    # await page.route(
    #     "**/*.{png,jpg,jpeg,gif,webp,svg,css,woff,woff2,eot,ttf}",
    #     lambda route: route.abort()
    # )
    # await page.goto(url)
    
    responce = await session.get(url, impersonate="chrome", timeout=15.0)
    
    responce.raise_for_status()
    
    soup = BeautifulSoup(responce.text, features="html.parser")
    
    benefits_list = []
    section_benefit_list = soup.find(attrs={"data-test": "sections-benefit-list"})
    elements_section_benefit_list = []
    if section_benefit_list:
        elements_section_benefit_list = section_benefit_list.find_all("li")
    
    for element in elements_section_benefit_list:
        if benefit := element.find(attrs={"data-test":"offer-badge-title"}):
                benefit_text = benefit.get_text(strip=True)
                benefits_list.append(benefit_text)
    
    # At first I made separetly for each element, and then I saw that it is a list    
    # Workplace
    # workplace = "None"
    # if section_benefit_list:
    #     if section_benefit_workplace := section_benefit_list.find(attrs={"data-test":"sections-benefit-workplaces"}):
    #         if workplace_soup := section_benefit_workplace.find(attrs={"data-test":"offer-badge-title"}):
    #             workplace = workplace_soup.get_text(strip=True)           
    # parsed.append({
    #     'workplace' : workplace,
    #     'contract' : contract,
    #     'schedule' : schedule,
    #     'employment_name' : name,
    #     'work_modes' : work_modes
    # })
    
    # Expected technologies
    expected_technologies_list = []
    
    aggregate_open_dictionary_model = soup.find(attrs={"data-test":"aggregate-open-dictionary-model"})
    
    if aggregate_open_dictionary_model:
        expected_technologies = aggregate_open_dictionary_model.find_all(attrs={"data-test":"item-technologies-expected"})
        for tech in expected_technologies:
            expected_technologies_list.append(tech.get_text(strip=True))
    
    # Responsibilities
    responsibilities_list = []
    
    section_responsibilities = soup.find(attrs={"data-test":"section-responsibilities"})
    
    if section_responsibilities:
        responsibilities = section_responsibilities.find_all("li")
        for resp in responsibilities:
            responsibilities_list.append(resp.get_text(strip=True))
    
    # Requirements
    requirements_list = []
    
    section_requirements = soup.find(attrs={"data-test":"section-requirements"})
    
    if section_requirements:
        requirements = section_requirements.find_all("li")
        for requ in requirements:
            requirements_list.append(requ.get_text(strip=True))
    
    # await page.close()           
    # for el in benefits_list:
    #     print(el)
    # for el in expected_technologies_list:
    #     print(el)
    # for el in responsibilities_list:
    #     print(el)
    # for el in requirements_list:
    #     print(el)      
    # await write_to_db(url, benefits_list, expected_technologies_list, responsibilities_list, requirements_list)
    return {
        "benefits": benefits_list,
        "expected_technologies": expected_technologies_list,
        "responsibilities": responsibilities_list,
        "requirements": requirements_list
    }
        
async def task(queue, pool, session):
    while not queue.empty():
        try:
            url = queue.get_nowait()
            scraped_data = await scrap_one_page(url, session)
            benefits = scraped_data["benefits"]
            tech = scraped_data["expected_technologies"]
            resp = scraped_data["responsibilities"]
            req = scraped_data["requirements"]
        except asyncio.QueueEmpty:
            break
        async with pool.connection() as conn:
            async with conn.cursor() as acur:
                await acur.execute("""
                INSERT INTO job_data (url, benefits, expected_technologies, responsibilities, requirements)
                VALUES (%(url)s, %(benefits)s, %(expected_technologies)s, %(responsibilities)s, %(requirements)s)
                ON CONFLICT(url)
                DO NOTHING
            """,
            {'url': url, 'benefits': benefits, 'expected_technologies': tech, 
            'responsibilities': resp, 'requirements': req})
        # print(f"Successfully saved: {url}")
        queue.task_done()
        await asyncio.sleep(0.1)
    
async def main():
    df = pd.read_csv('url.csv')
    queue = asyncio.Queue()
    df = df.drop_duplicates(subset=[df.columns[0]])
    url_list = [row[0] for row in df.itertuples(index=False)]
    queue = asyncio.Queue()
    for url in url_list:
        await queue.put(url)
        
    print(f"Loaded {queue.qsize()} URLs into memory queue.")
    
    async with psycopg_pool.AsyncConnectionPool(connect, max_size=25) as pool:
        # async with async_playwright() as p:
        #     optimized_args = [
        #         "--disable-blink-features=AutomationControlled", # Bypass basic bot detection
        #         "--disable-gpu",                                 # Turn off graphics rendering calculation
        #         "--disable-dev-shm-usage",                       # Prevent memory crashes in docker/linux
        #         "--no-first-run",                                # Skip welcome screens
        #         "--no-sandbox",                                  # Speed up execution environment
        #         "--blink-settings=imagesEnabled=false",          # Structural fallback to prevent images
        #     ]
        #     browser = await p.chromium.launch_persistent_context(
        #         user_data_dir="./user_data",
        #         channel="chrome",
        #         headless=True,
        #         # This argument helps bypass some automation detections
        #         args=optimized_args
        #     )
        async with AsyncSession() as session:
            tasks = [
                asyncio.create_task(task(queue, pool, session))
                for i in range(25)
            ]
            await queue.join()
            
            for w in tasks:
                w.cancel()
                
if __name__=="__main__":
    # asyncio.run(main())
    asyncio.run(scraping_urls())
    # asyncio.run(scrap_one_page())
    

