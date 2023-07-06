import time
from bs4 import BeautifulSoup as bs 
from selenium import webdriver
from selenium.webdriver.chrome.service import Service 
from selenium.webdriver.chrome.options import Options

import getAni

def getAniSeasonData(year: int, season: str) -> tuple:
## get link
    url = f'https://anilist.co/search/anime?format=TV&year={year}&season={season}'
    print(url)

    ## open browser
    options = Options()
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    browser = webdriver.Chrome(options=options)
    browser.get(url)
    
    ## scroll to bottom
    ## Get scroll height
    last_height = browser.execute_script("return document.body.scrollHeight")

    while True:
        # Scroll down to the bottom.
        browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Wait to load the page.
        time.sleep(.5)

        # Calculate new scroll height and compare with last scroll height.
        new_height = browser.execute_script("return document.body.scrollHeight")

        if new_height == last_height:
            break

        last_height = new_height

    ## get html
    html = browser.page_source
    soup = bs(html, 'html.parser')

    ## close browser
    browser.quit()

    ## find links
    links = soup.find_all('a', {'class': 'cover'}, href=True)
    coverLinks = [a['href'] for a in links]

    ## get each anilist entry
    entries = []
    for link in coverLinks:
        time.sleep(0.25)
        print(link)
        try:
            entries.append(getAni.getAniData(link, getPrequel=True))
        except Exception as e:
            print(e)
    
    return entries

if __name__ == '__main__':
    seasons = {
        0: 'WINTER',
        1: 'SPRING',
        2: 'SUMMER',
        3: 'FALL'
    }

    year = None
    while year == None:
        yearIn = input('Please input a year of anime you want (ie. 2023)\n')
        try:
            year = int(yearIn)
        except ValueError:
            print('Please input a number')
            continue

    seasonNum = None
    while seasonNum == None:
        print('Please select a season of anime (0-3):')
        for s in seasons:
            print(f' - {s}: {seasons[s]}')

        seasonIn = input()
        try:
            seasonIn = int(seasonIn)
        except ValueError:
            print('Please input a number')
            continue

        if seasonIn in seasons:
            seasonNum = int(seasonIn)

    ## run script
    anilist = getAniSeasonData(year=year, season=seasons[seasonNum])
    ## sort by English title
    anilist.sort(key=lambda x: x.title)

    ## export output
    output = 'entries:\n'
    output += ''.join([str(a) for a in anilist])
    print(output)
    ## write to file
    with open(f'yamlFiles/{year}-{seasonNum}-{seasons[seasonNum]}-Anime.yaml', 'w', encoding='utf-8') as f:
        f.write(output)