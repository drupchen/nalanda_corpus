#! /usr/bin/env python3

import sys
from bisect import bisect_left

if len(sys.argv) < 2:
    print("Run this script with the file you want to segment as argument!")
    print("Doing nothing...")
    exit(1)

suffixes = {
    'འི': True,
    'འོ': True,
    'འང': True,
    'འམ': True,
    'ར': True,
    'ས': True
    }

second_suffixes = {
    'གས': True,
    'ངས': True,
    'བས': True,
    'མས': True
    }

chars_to_insert = {
    'word': ' ',
    'error': '!',
    'particle': '+',
    'suffix': '-'
}

lists = {}
lists_len = {}

def addList(listName, fileName):
    global lists, lists_len
    if not listName in lists:
        lists[listName] = []
    with open(fileName, encoding='utf-8') as f:
        for line in f:
            lists[listName].append(line.strip().strip('་'))
    lists[listName] = sorted(lists[listName])
    lists_len[listName] = len(lists[listName])

addList('particles', 'src/particles.txt')
addList('words', 'src/verbs.txt')
addList('words', 'src/TDC.txt')

#print(lists['words'])

def search(entry, listName):   # can't use a to specify default for hi
    global lists, lists_len
    # using bisect here divides computation time by a huge amount
    pos = bisect_left(lists[listName],entry,0,lists_len[listName])
    return (True if pos != lists_len[listName] and lists[listName][pos] == entry else False)
    

# returns False or the length of the suffix it had to remove to find the string
def lookupStr(str):
    if len(str) == 0:
        return False
    if search(str, 'particles'):
        return {'suffixLength': 0, 'type': 'particle', 'str': str}
    if search(str, 'words'):
        return {'suffixLength': 0, 'type': 'word', 'str': str}
    suffixLength = getSuffixLength(str)
    if suffixLength == 0:
        return False
    strNoSuffix = str[0: -suffixLength]
    if not str:
        return False
    if search(strNoSuffix+'འ', 'words'):
        return {'suffixLength': suffixLength, 'type': 'word', 'ashung': True, 'str': str}
    if search(strNoSuffix, 'words'):
        return {'suffixLength': suffixLength, 'type': 'word', 'str': str}
    if search(strNoSuffix, 'particles'):
        return {'suffixLength': suffixLength, 'type': 'particle', 'str': str}
    return False

# get the length of the suffix (or 0)
def getSuffixLength(str):
    global suffixes, second_suffixes
    if str[-2:] in second_suffixes and len(str) > 3 and not str[-3] == '་':
        return 0
    if str[-2:] in suffixes:
        return 2
    if str[-1:] in suffixes:
        return 1
    return 0

def isTibetanLetter(c):
    if (c >= 'ༀ' and c <= '༃') or (c >= 'ཀ' and c <= 'ྼ'):
       return True
    return False

def getNextSyllablesString(str, idx, nbSyllables):
    if not str or len(str) <= idx:
        return False
    res = ''
    initialState = True
    nbTshegs = 0
    while (idx < len(str) and nbTshegs < nbSyllables):
        if isTibetanLetter(str[idx]):
            initialState = False
            res += str[idx]
        if str[idx] == '༌' or str[idx] == '་' and initialState == False:
            nbTshegs = nbTshegs + 1
            if (nbTshegs < nbSyllables):
                res += str[idx]
        idx = idx + 1
    return res

# returns indexes in clean string
def lookupNextSyllablesString(str):
    res= lookupStr(str)
    if res:
        return res
    else:
        lastTshegIndex = str.rfind('་',1)
        if not lastTshegIndex == -1:
            return lookupNextSyllablesString(str[:lastTshegIndex])
        else:
            return {'type': 'error', 'suffixLength': 0, 'str': str}

def printSegmentedNextStr(str, lenstr, idx, lookupNextStr, typeToPrint):
    global output
    """This function is where the priting logic happens:
        nextTypeToPrint is the type of the last lookup, which we usually didn't write
        because we want 'word+particle ', not 'word particle+'
    """
    initialIdx = idx
    nextSyllIdx = 0
    nextSyllLen = len(lookupNextStr['str'])
    # spaghetti plate for word+particle handling
    nextTypeToPrint = lookupNextStr['type']
    if typeToPrint:
        if idx < lenstr-1 and str[idx] == '་':
            output += '་'
            idx += 1
            initialIdx += 1
        if lookupNextStr['type'] == 'particle':
            output += chars_to_insert['particle']
        else:
            output += chars_to_insert[nextTypeToPrint]
    elif lookupNextStr['type'] == 'particle':      
        nextTypeToPrint = nextTypeToPrint
    initialState = True
    while (idx < lenstr and nextSyllIdx < nextSyllLen):
        if isTibetanLetter(str[idx]) or ((not initialState) and (str[idx] == '༌' or str[idx] == '་')):
            initialState = False
            nextSyllIdx = nextSyllIdx + 1
        idx = idx + 1
    if idx == lenstr:
        return {'idx': idx, 'nextTypeToPrint': None}
    # spaghetti plate for suffix handling
    output += str[initialIdx:idx-lookupNextStr['suffixLength']]
    if not lookupNextStr['suffixLength'] == 0:
        if 'ashung' in lookupNextStr:
            output += 'འ'
        output += chars_to_insert['suffix']
        output += str[idx-lookupNextStr['suffixLength']:idx]
    return {'idx': idx, 'nextTypeToPrint': nextTypeToPrint} 

def printSegmented(str):
    global output
    idx = 0
    lenstr = len(str)
    nextTypeToPrint = None
    while (idx < lenstr):
        nextStr = getNextSyllablesString(str, idx, 4)
        if nextStr == '':
            break
        lookupNextStr = lookupNextSyllablesString(nextStr)
        newValues = printSegmentedNextStr(str, lenstr, idx, lookupNextStr, nextTypeToPrint)
        nextTypeToPrint = newValues['nextTypeToPrint']
        if newValues['idx'] == idx:
            print("Achtung, ich bin kapput2!", file=sys.stderr)
            return
        idx = newValues['idx']
    output += '\n'

test = 'དཀར་ཆ་གི་དཀར་ཆར་ནོ་'

def main():
    global output
    with open(sys.argv[1], 'r', encoding='utf-8') as content_file:
        content = content_file.read()
    printSegmented(content)
    with open(sys.argv[1].split('.')[0]+'_segmented.txt', 'w', encoding='utf-8') as f:
        f.write(output)

output = ''
main()
