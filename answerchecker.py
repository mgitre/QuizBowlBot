# -*- coding: utf-8 -*-
"""
Created on Mon Oct 26 18:34:22 2020

@author: Max
"""

import unicodedata, re
from nltk.stem import PorterStemmer
from custom_levenshtein import levenshtein

stopwords = "derp rofl lmao lawl lole lol the prompt on of is a in on that have for at so it do or de y by accept any and book battle".split(' ')
def removeDiacritics(string):
    return ''.join(c for c in unicodedata.normalize('NFD', string)
                  if unicodedata.category(c) != 'Mn')

def parseAnswer(answer):
    answer = re.sub("[\[\]\<\>\{\}][\w\-]+?[\[\]\<\>\{\}]", "", answer)
    
    clean = [part.strip() for part in re.split("[^\w]or[^\w]|\[|\]|\{|\}|\;|\,|\<|\>|\(|\)", answer)]
    clean = [part for part in clean if part!='']
    
    pos = []
    neg = []
    
    for part in clean:
        part = removeDiacritics(part)
        part = re.sub("\"|\'|\“|\”|\.|’|\:", "", part)
        part = part.replace("-"," ")
        #print(part, end=" ")
        
        if re.search("do not|dont", part):
            neg.append(part)
        elif re.search("accept", part):
            comp = re.split("before|until", part)
            if len(comp) > 1:
                neg.append(comp[1])
            pos.append(comp[0])
        else:
            pos.append(part)
    return [pos,neg]

def replaceNumber(word):
    if re.search("\d+nd|\d+st|\d+th|\d+rd", word):
        return int(re.sub("nd|st|th|rd","",word))
    if word in ['zero', 'zeroeth', 'zeroth']:
        return 0
    if word in ['one', 'first',' i']:
        return 1
    if word in ['two', 'second', 'twoth', 'ii']:
        return 2
    if word in ['three', 'third', 'turd', 'iii', 'iiv']:
        return 3
    if word in ['forth', 'fourth', 'four', 'iiii', 'iv']:
        return 4
    if word in ['fifth', 'five', 'v']:
        return 5
    if word in ['sixth', 'six', 'vi']:
        return 6
    if word in ['seventh', 'seven', 'vii']:
        return 7
    if word in ['eight', 'eighth', 'viii', 'iix']:
        return 8
    if word in ['nine', 'nein', 'ninth', 'ix', 'viiii']:
        return 9
    if word in ['tenth', 'ten', 'x']:
        return 10
    if word in ['eleventh', 'eleven', 'xi']:
        return 11
    if word in ['twelfth', 'twelveth', 'twelve', 'xii']:
        return 12
    if word in ['thirteenth', 'thirteen', 'xiii', 'iixv']:
        return 13
    if word in ['fourteenth', 'fourteen', 'ixv', 'xiiii']:
        return 14
    return word

def stem(word):
    return PorterStemmer().stem(re.sub("[^\w]","", re.sub("ez$","es", word)))

def splitWords(text):
    li = [word.strip() for word in re.split("[\s\/\-]+",text.lower())]
    words = [stem(word) for word in li if (not word in stopwords and word!="")]
    return words
    
def isPerson(answer):
    canon = [name for name in re.split("\s+",answer) if len(name) > 3]
    caps = [name for name in canon if re.search("[A-Z]", name)]
    return len(caps) == len(canon)

def reduceLetter(letter):
    if letter in ['z', 's', 'k', 'c']:
        return "s"
    if letter in ['e', 'a', 'o', 'u', 'y', 'i']:
        return "e"
    return letter

def reduceAlphabet(word):
    return "".join([reduceLetter(letter) for letter in word])

def levens(a,b):
    return levenshtein(reduceAlphabet(a), reduceAlphabet(b))

def checkWord(word, li):
    scores = []
    for i in range(len(li)):
        if len(li[i])==0:
            continue
        valid = li[i]
        score = levens(valid, word)
        scores.append([score, len(valid)-score, len(valid), valid])
    
    if len(scores) == 0:
        return ''
    
    scores = sorted(scores, key=lambda x: x[0])
    
    score, real, length, valid = scores[0]
    
    frac = real/length
    
    if frac >= 0.8 + 0.05*(length>4):
        return valid
    return ''

def advancedCompare(inputText, p, questionWords):
    is_person = isPerson(p.strip())
    li = [word for word in splitWords(p) if not word in questionWords]
    valid_count = 0
    invalid_count = 0
    
    for word in inputText:
        value = 1
        result = checkWord(word, li)
        if is_person and result in stopnames and not 'gospel' in li:
            value = 0.5
        if result:
            valid_count += value
        else:
            invalid_count += value
    return valid_count - invalid_count >= 1

def rawCompare(compare, p):
    compare = re.sub("[^\w]", "", compare.lower()).replace("accept","")
    p = re.sub("[^\w]", "", p.lower()).replace("accept","")
    
    minlen = min(len(compare), len(p))
    
    diff = levens(compare[0:minlen], p[0:minlen])
    
    accuracy = 1 - (diff / minlen)
    
    if minlen >= 4 and accuracy >= 0.8:
        return True
    return False

def checkAnswer(compare, answer, question=""):
    compare = re.sub("\{|\}","",compare)
    answer = re.sub("\{|\}","",answer)
    
    question = removeDiacritics(question).strip()
    answer = removeDiacritics(answer).strip()
    compare = removeDiacritics(compare).strip()
    
    questionWords = splitWords(question)
    inputText = [word for word in splitWords(compare) if not word in questionWords]
    [pos, neg] = parseAnswer(answer)
    
    responses = []
    
    for p in pos:
        if len(re.sub("[^0-9]","",compare)) == 4:
            year = re.sub("[^0-9]","",compare)
            compyr = re.sub("[^0-9]","",p)
            if year == compyr:
                responses.append(True)
        else:
            responses.append(advancedCompare(inputText, p, questionWords))
            responses.append(rawCompare(compare, p))
    
    for r in responses:
        if r:
            return True
    return False

stopnames = splitWords("ivan james john robert michael william david richard charles joseph thomas christopher daniel paul mark donald george steven edward brian ronald anthony kevin jason benjamin mary patricia linda barbara elizabeth jennifer maria susan margaret dorothy lisa karen henry harold luke matthew")
