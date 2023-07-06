import re
import requests
import roman
import sys
from bs4 import BeautifulSoup as bs
from ordered_set import OrderedSet
from thefuzz import fuzz
from urllib import parse

sys.stdout.reconfigure(encoding='utf-8')

anilistExp = re.compile(r'\/?anime\/([0-9]+)', re.IGNORECASE)
seasonExp = re.compile(r'(?:([0-9]+)(?:st|nd|rd|th) Season)|(?:Season ([0-9]+))|(?:Part ([0-9])+)|(?:Cour ([0-9]+))', re.IGNORECASE)
endNumExp = re.compile(r'[a-z0-9 ]+ ((?:(?:[0-9]+)$)|(?:(?=[MDCLXVI])M*(?:C[MD]|D?C{0,3})(?:X[CL]|L?X{0,3})(?:I[XV]|V?I{0,3})$))', re.IGNORECASE)
romajiExp = re.compile(r'([aeiou]|[bkstgzdnhpmr]{1,2}[aeiou]|(?:sh|ch|j|ts|f|y|w|k)(?:y[auo]|[aeiou])|n|\W|[0-9])+', re.IGNORECASE)

class AnilistEntry:
    def __init__(self, title: str):
        self.title = title
        self.synonyms = set()
        self.seasons = OrderedSet()
    def __repr__(self) -> str:
        title = self.title.replace('"', '\\"')
        string = f'  - title: "{title}"\n'
        if len(self.synonyms):
            string += '    synonyms:\n'
            for syn in self.synonyms:
                synonym = syn.replace('"', '\\"')
                string += f'      - "{synonym}"\n'
        string += '    seasons:\n'
        for season in self.seasons:
            string += f'      - season: {season[0]}\n'
            string += f'        anilist-id: {season[1]}\n'
        return string

def first(iterable, func=lambda L: L is not None, **kwargs):
    it = (el for el in iterable if func(el))
    if 'default' in kwargs:
        return next(it, kwargs['default'])
    return next(it) # no default so raise `StopIteration`

def getAniData(url: str, getPrequel: bool = False) -> AnilistEntry:
    season = 1
    anilistId = None
    endNum = None
    matchPercentage = 30
    ## check valid link
    parsed_uri = parse.urlparse(url)
    
    ## check url for ######
    if url.isnumeric():
        anilistId = int(url)
    ## check url for anilist.co/anime/######
    elif parsed_uri.netloc == 'anilist.co':
        splitPath = parsed_uri.path[1:].split('/')
        if splitPath[0] != 'anime':
            raise Exception('provided url does not contain an anime')
        
        if not splitPath[1].isnumeric():
            raise Exception('provided url does not contain an anime entry')
        anilistId = int(splitPath[1])
    ## check url for /anime/######/
    else:
        anilistExpSearch = anilistExp.search(url)
        if anilistExpSearch is not None:
            anilistId = int(anilistExpSearch.group(1))
    ## not valid url
    if not anilistId:
        raise Exception('provided url is not of anilist.co')
    
    ## new url
    newUrl = f'https://anilist.co/anime/{anilistId}'

    ## get link
    r = requests.get(newUrl)

    ## check valid status code
    if r.status_code != 200:
        raise Exception('provided url does not lead to a valid location')
    
    ## parse html
    soup = bs(r.content, 'html.parser')

    ## find Romaji title
    romajiParent = soup.find('div', {'class': 'type'}, string="Romaji").parent
    romajiName = romajiParent.find('div', {'class': 'value'}).text.strip()

    ## find English title
    engHeader = soup.find('div', {'class': 'type'}, string="English")
    if engHeader:
        engName = engHeader.parent.find('div', {'class': 'value'}).text.strip()
    else:
        engName = romajiName

    ## check for season number in title
    search = seasonExp.search(engName)
    if search is not None:
        season = max(int(first(search.groups())), season)
    search = seasonExp.search(romajiName)
    if search is not None:
        season = max(int(first(search.groups())), season)
    
    ## check for ending number
    search2 = endNumExp.search(engName)
    if search2 is not None:
        try:
            endNum = int(first(search2.groups())) or endNum
        except ValueError:
            ## roman numeral
            endNum = roman.fromRoman(first(search2.groups()).upper()) or endNum
    search2 = endNumExp.search(romajiName)
    if search2 is not None:
        try:
            endNum = int(first(search2.groups())) or endNum
        except ValueError:
            ## roman numeral
            endNum = roman.fromRoman(first(search2.groups()).upper()) or endNum

    ## create new entry 
    alEntry = AnilistEntry(engName)

    ## find synoynms
    synHeader = soup.find('div', {'class': 'type'}, string='Synonyms')
    if synHeader:
        synList = synHeader.parent.find_all('span')
    
        for syn in synList:
            synTitle = syn.text.strip()
            # check fuzzy match or romaji (only ascii characters)
            if synTitle.isascii() and (fuzz.ratio(synTitle, engName) > matchPercentage or fuzz.ratio(synTitle, romajiName) > matchPercentage or romajiExp.fullmatch(synTitle)):
                alEntry.synonyms.add(synTitle)
            
            # check for season number in synonyms
            search = seasonExp.search(synTitle)
            if search is not None:
                season = max(int(first(search.groups())), season)
            
            # check for ending number in synonyms
            search2 = endNumExp.search(synTitle)
            if search2 is not None:
                try:
                    endNum = int(first(search2.groups())) or endNum
                except ValueError:
                    ## roman numeral
                    endNum = roman.fromRoman(first(search2.groups()).upper()) or endNum

    ## add Romaji as synonym
    ## check if different from English name
    if romajiName != engName:
        alEntry.synonyms.add(romajiName)

    alEntry.seasons.add((season, anilistId, endNum))

    ## recursively find the prequels until the first season
    if getPrequel == True:
        if season > 1 or endNum:
            ## find link of prequel
            linkParent = soup.find('div', string="Prequel")
            if linkParent:
                link = linkParent.find_parent('a', {'class': 'cover'}, href=True)['href']
                fullLink = 'https://anilist.co' + link
                ## get prequel entry and append
                newAlEntry = getAniData(url=fullLink, getPrequel=True) 
                newAlEntry.seasons |= alEntry.seasons

                return newAlEntry
            ## no prequels
            return alEntry

    ## no prequels
    return alEntry

if __name__ == '__main__':
    url = input('Please input the url of the anilist page you are trying to get:\n')
    print(getAniData(url=url, getPrequel=True))

## TODO: ADD START AT SUPPORT