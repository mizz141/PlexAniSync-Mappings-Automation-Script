import os
import yaml

from getAni import AnilistEntry

    
def mergeYaml(directory: str) -> None:
    yamlList = []
    for filename in os.listdir(directory):
        f = os.path.join(directory, filename)
        with open(f, 'r', encoding='utf-8') as file:
            yamlList.append(yaml.safe_load(file))

    # print(yamlList[0])

    anilistEntries = {}
    for yamlObj in yamlList:
        entries = yamlObj['entries']
        for entry in entries:
            if entry['title'] in anilistEntries:
                if 'synonyms' in entry:
                    anilistEntries[entry['title']].synonyms |= set(entry['synonyms'])
                for season in entry['seasons']:
                    anilistEntries[entry['title']].seasons.add(tuple(season.values()))
            else:
                newEntry = AnilistEntry(entry['title'])
                if 'synonyms' in entry:
                    newEntry.synonyms = set(entry['synonyms'])
                # newEntry.seasons = entry['seasons']
                for season in entry['seasons']:
                    newEntry.seasons.add(tuple(season.values()))
                anilistEntries[entry['title']] = newEntry
            # try:
            #     print(anilistEntries)
            # except TypeError:
            #     print(anilistEntries[entry['title']].seasons)
            #     raise Exception


    sortedYaml = sorted(anilistEntries.items(), key=lambda item: item[0])
    output = 'entries:\n'
    for key, value in sortedYaml:
        output += str(value)
    with open(f'customMappings.yaml', 'w', encoding='utf-8') as f:
        f.write(output)

if __name__ == '__main__':
    mergeYaml('./yamlFiles')