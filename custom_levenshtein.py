# -*- coding: utf-8 -*-
"""
Created on Mon Oct 26 20:36:15 2020

@author: Max
"""

qwerty = "qwertyuiopasdfghjkl;zxcvbnm,./";
vowels='aeiouy'
parseltongue='zsck'


def letter_coord(letter):
    index = qwerty.find(letter.lower())
    if index < 0:
        return [-1,-1]
    return [index % 10, int(index/10)]

def letter_cost(A, B):
    if A.lower()==B.lower():
        return 0
    if A in [str(i) for i in range(10)] and B in [str(i) for i in range(10)]:
        return 1.2
    if (A in vowels and B in vowels) or (A in parseltongue and B in parseltongue):
        return 0.2
    axy, bxy = letter_coord(A), letter_coord(B)
    
    if axy[0] < 0 or bxy[0] < 0:
        return 1
    
    dx, dy = axy[0]-bxy[0], axy[1]-bxy[1]
    
    if abs(dx) > 1 or abs(dy) > 1:
        return 1
    if dy==0:
        return 0.5
    return 0.7

def levenshtein(a,b):
    
    if len(a)==0:
        return len(b)
    if len(b)==0:
        return len(a)
    d = [[0 for i in range(len(b)+1)] for j in range(len(a)+1)]
    for i in range(len(a)+1):
        d[i][0] = i
    for j in range(len(b)+1):
        d[0][j] = j
    
    for i in range(1,len(a)+1):
        for j in range(1, len(b)+1):
            cost = letter_cost(a[i-1], b[j-1])
            d[i][j] = min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + cost )
            
            if i>1 and j>1 and a[i-1] == b[j-2] and a[i-2]==b[j-1]:
                d[i][j] = min(d[i][j], d[i-2][j-2] + 0.4)
    return d[len(a)][len(b)]