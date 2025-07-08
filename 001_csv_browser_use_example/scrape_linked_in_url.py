import pandas as pd
import asyncio
from browser_use import Browser, BrowserConfig
from browser_use.browser.context import BrowserContextConfig

from playwright.async_api import async_playwright

import random
from typing import List, Dict
import time

import os


class Scraper:

    def __init__(self, url_column:str):
        self.browser = None
        self.playwright = None
        self.url_column = url_column 

    async def init_browser(self):
        self.playwright = await async_playwright().start()
        self.browser = await Browser()._setup_browser(self.playwright)

    async def close_browser(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def extract_linked_in_url(self, url:str) -> Dict[str, str]:
        #print(f"going to scrape: {url}")
        try:
            self.context = await self.browser.new_context()
            page = await self.context.new_page()

            await page.goto(url, wait_until='domcontentloaded', timeout=30000)

            initial_url = page.url

            # wait for the body to be loaded
            await page.wait_for_selector('body', timeout=10000)

            # click first link item in google (after the first one at n=0 in the search bar) and retrieve the private linkedin url
            locator = page.get_by_text('LinkedIn', exact=False).nth(1)
            await locator.click()

            url_found = page.url
            await page.close()

            # make sure that after the click actions, that the url_found is different than the initial_url
            if url_found != initial_url:
                return url_found
            else:
                # if url_found is the same as the initial_url, return blank since no meaningful prediction was issued
                return ''
    
        except Exception as error:
            print(error)
            print("some sort of error response, sending over blank")
            return ''

    async def scrape_websites(self, urls: List[str]) -> Dict[str,str]:
        if not self.browser:
            print("init ")
            await self.init_browser()

        results_list = []

        for i, url in enumerate(urls):
            print(f"step: {i}; procesing url: {url}")

            # doing random sleep interval to evade detection of scraping
            random_delay_sec = random.uniform(2,7)
            time.sleep(random_delay_sec)
            
            linked_in_url = await self.extract_linked_in_url(url)
            print(f"detected_url:  {linked_in_url}")

            result = {
                'target_url': url,
                'linked_in_url': linked_in_url
            }

            results_list.append(result)

        return results_list


async def main(df_input: pd.DataFrame()):
    
    # load the scraper class
    scraper = Scraper('url_search')

    try:
        # if main is invoked using multiprocessing pool, the result predictions may arrive out of order. this makes sure they match the input data order.
        results_list = await scraper.scrape_websites(df_input[scraper.url_column].tolist())
        for result in results_list:
            try:
                # insert the predicted linkedin url in the positions where the search url column value matches the predicted url input value
                print(f"applying results mask for dictionary item: {result}")
                mask = df_input[scraper.url_column] == result['target_url']
                df_input.loc[mask, 'predicted_url'] = result['linked_in_url']
            except:
                pass

        return df_input

    except Exception as error:
        print(error)

    finally:
        return df_input
        #await scraper.close_browser()


if __name__ == '__main__':

    # https://scrapingant.com/blog/web-scraping-playwright-python-part-4

    # input path for data to construct target urls and scrape linkedin url from
    fi = 'input_attendees_truncated.csv'

    # output path for input data with the addition of predicted linkedin url
    fo = fi.replace('.csv', '_output.csv')

    # read the input file to dataframe
    df_input = pd.read_csv(fi)

    # construct a target search url string for each row of the input dataframe
    df_input['url_search'] = "http://www.google.com/search?q=LinkedIn" + " " + df_input['Name'] + " " + df_input['Title'] + " " + df_input['Company']

    # process the dataframe using browser use scripts and playwright
    df_processing = asyncio.run(main(df_input))

    # write out the resulting prediction to the outfil
    df_processing.to_csv(fo, index=False)