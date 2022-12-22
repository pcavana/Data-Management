from __future__ import annotations

import requests
from bs4 import NavigableString as SoupStr
from bs4 import BeautifulSoup as bs
import bs4

def printSoupContent(soup:bs):
    print(soup.contents)
    contentsType = []
    for el in soup.contents:
        contentsType.append(type(el))
    print(contentsType)

def soup(url:str):
    """Get a BeautifulSoup object from an URL"""
    response = requests.get(url)
    if not response.ok:
        raise Exception("GET request fail for page " + url)
    return bs(response.content, "html5lib") # pip install html5lib, required for reading <br> tags as <br/> tags

def wiseCondition(leftStr:SoupStr|str, rightStr:SoupStr|str):
    """True if there should be nothing between the two strings when merging together"""
    return leftStr.endswith(('(', '[', '{')) or rightStr.startswith((',', '.', ':', ';', ')', ']', '}', '"', "'", '?', '!')) or leftStr == "" or rightStr == ""

def mergeStringElement(parent:bs, index:int, left=True, right=True, joinStr:str|SoupStr=" ", wise=True):
    """Merge the string element parent.contents[i] with the left and the right elements"""
    merged = False
    # get and check element
    strElement = parent.contents[index]
    if not isinstance(strElement, bs4.element.NavigableString):
        raise ValueError("Element at index " + str(index) + " of Parent argument is not a NavigableString (name=" + strElement.name + ")")
    strElementText = strElement.strip()
    # previous element
    leftEl = None
    leftElText = None
    if left and 0 <= index-1 < len(parent.contents) and isinstance(parent.contents[index-1], bs4.element.NavigableString):
        leftEl = parent.contents[index-1]
        leftElText = leftEl.strip()
    # next element
    rightEl = None
    rightElText = None
    if right and 0 <= index+1 < len(parent.contents) and isinstance(parent.contents[index+1], bs4.element.NavigableString):
        rightEl = parent.contents[index+1]
        rightElText = rightEl.strip()
    # merge strings
    if left and leftEl:
        if wise and wiseCondition(leftElText, strElementText):
            strElementText = SoupStr(leftElText + strElementText)
        else:
            strElementText = SoupStr(leftElText + joinStr + strElementText)
        strElement.replace_with(strElementText)
        # update strElement after replacement
        strElement = parent.contents[index]
        leftEl.extract()
        merged = True
    if right and rightEl:
        if wise and wiseCondition(strElement, rightEl):
            strElementText = SoupStr(strElementText + rightElText)
        else:
            strElementText = SoupStr(strElementText + joinStr + rightElText)
        strElement.replace_with(strElementText)
        # update strElement after replacement
        if leftEl and left:
            strElement = parent.contents[index-1]
        else:
            strElement = parent.contents[index]
        rightEl.extract()
        merged = True
    if strElementText.strip() == "":
        strElement.extract()
        # in a case where contents are like [<tag/>, " ", <tag/>] nothing is merged
        # but with this final check the result will be [<tag/>, <tag/>]
        # consider this a merge, because merge = False means that no changes were made
        merged = True
    return merged

def mergeStringElements(soup:bs, joinStr=" ", wise=True):
    """Merge all the adjacent children of the given element if strings"""
    # TODO don't keep tag order option
    decrease = 0
    for i in range(len(soup.contents)-1):
        i -= decrease
        # if merge is successful, len(soup.contents) will be decreased
        # -> keep track of the changes to the contents and adapt index
        try:
            if mergeStringElement(soup, i, left=False, joinStr=joinStr, wise=wise):
                decrease += 1
        except ValueError:
            # means that the element at index i was not a NavigableString,
            # just ignore
            pass

def handleLinebreaks(soup:bs, wiseReplace:str=None):
    """Remove <br> or <br/> tags from the first depth level children"""
    for br in soup.find_all("br", recursive=False):
        i = soup.index(br)
        br.replace_with(SoupStr(""))
        mergeStringElement(soup, i, joinStr=wiseReplace if wiseReplace else " ")

def handleSpan(soup:bs, extract=True):
    """Extract contents of <span> tags from the first depth level children"""
    for span in soup.find_all("span", recursive=False):
        i = soup.index(span)
        if extract:
            if span.string and span.string.strip() != "":
                span.replace_with(SoupStr(span.string))
            elif span.has_attr("title"):
                span.replace_with(SoupStr(span["title"]))
            else:
                span.replace_with(SoupStr(""))
        else:
            span.replace_with(SoupStr(""))
        mergeStringElement(soup, i)

def handleSmall(soup:bs, extract=True):
    """Extract contents of <small> tags from the first depth level children"""
    for small in soup.find_all("small", recursive=False):
        i = soup.index(small)
        if extract:
            if small.string and small.string.strip() != "":
                small.replace_with(SoupStr(small.string))
            else:
                small.replace_with(SoupStr(""))
        else:
            small.replace_with(SoupStr(""))
        mergeStringElement(soup, i)

def handleItalic(soup:bs, extract=True):
    """Extract contents of <i> tags from the first depth level children"""
    for italic in soup.find_all("i", recursive=False):
        i = soup.index(italic)
        if extract:
            if italic.string and italic.string.strip() != "":
                italic.replace_with(SoupStr(italic.string))
            else:
                italic.replace_with(SoupStr(""))
        else:
            italic.replace_with(SoupStr(""))
        mergeStringElement(soup, i)

def handleStrong(soup:bs, extract=True):
    """Extract contents of <strong> tags from the first depth level children"""
    for strong in soup.find_all("strong", recursive=False):
        i = soup.index(strong)
        if extract:
            if strong.string and strong.string.strip() != "":
                strong.replace_with(SoupStr(strong.string))
            else:
                strong.replace_with(SoupStr(""))
        else:
            strong.replace_with(SoupStr(""))
        mergeStringElement(soup, i)

def handleLinks(soup:bs, replaceWithText=True):
    """Remove <a> tags from the first depth level children"""
    for a in soup.find_all("a", recursive=False):
        i = soup.index(a)
        if replaceWithText:
            if a.string and a.string.strip() != "":
                a.replace_with(SoupStr(a.string))
            elif a.has_attr("title"):
                a.replace_with(SoupStr())
            elif a.has_attr("href"):
                a.replace_with(SoupStr(a["href"]))
            else:
                a.replace_with(SoupStr(""))
        else:
            a.replace_with(SoupStr(""))
        mergeStringElement(soup, i)

def handleSups(soup:bs):
    """Remove <sup> tags from the first depth level children"""
    for sup in soup.find_all("sup", recursive=False):
        i = soup.index(sup)
        sup.replace_with(SoupStr(""))
        mergeStringElement(soup, i)

def handleP(soup:bs):
    """Extract contents of <p> tags from the first depth level children"""
    for p in soup.find_all("p", recursive=False):
        i = soup.index(p)
        mergeStringElements(p)
        # replace_with accept an arbitrary number of parameters
        # *p.contents expands the array of contents
        # this way replace_with will receive the list of elements and not a list containing the list of elements
        if len(p.contents) > 0:
            p.replace_with(*p.contents)
            if isinstance(soup.contents[i], bs4.element.NavigableString):
                mergeStringElement(soup, i)
        else:
            p.decompose()
            # i-1 because if p was the last element of soup, i is out of range
            if isinstance(soup.contents[i-1], bs4.element.NavigableString):
                # left=False because the element i-2 is not adjacent to p, so it must not be modified
                mergeStringElement(soup, i-1, left=False)
