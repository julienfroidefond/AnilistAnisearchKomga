import time
from lxml import etree
from lxml.etree import ParserError
from playwright.sync_api import sync_playwright

from utils import printC

summarySourceLang = [" Quelle: ", " Quelle:", "Quelle:", " Source: ", " Source:", "Source:"]
runningLang = ["Laufend", "Ongoing", "Corriente", "En cours", "In corso", "放送", "放送（連載）中"]
abandonedLang = ["Abgebrochen", "Aborted", "Cancelado", "Annulé", "Abbandonato", "打ち切り"]
endedLang = ["Abgeschlossen", "Completed", "Completado", "Terminé", "Completato", "完結"]
tagTexts = ["Hauptgenres", "Main genres", "Género principal", "Principaux genres", "Generi principali", "メインジャンル"]
noSummaryLang = ["Damit hilfst Du der gesamten deutschsprachigen Anime und Manga-Community", "We’re looking forward to your contributions", "Con esto ayudas a toda la comunidad de Anime y Manga", "Nous attendons avec impatience tes contributions", "Non vediamo l’ora di ricevere i tuoi contributi", "皆様からのご投稿をお待ちしております"]
blurbLang = ["Klappentext", "Blurb", "Texto de presentación", "Texte du rabat", "Testo della bandella"]

#out = open("out.txt", "w", encoding='utf-8')
#out.write(tree.tostring(tree.getroot()).content.decode(sys.stdout.encoding, errors='replace'))
#out.close()

#printC(getURLfromSearch("adekan", anisearchlang))

class metadata:
    def __init__(self):
            self.status = ""
            self.summary = ""
            self.publisher = ""
#            self.agerating = ""
            self.genres = []
            self.tags = []
            self.isvalid = False

def getBaseURL(anisearchlang):
    if(anisearchlang == "German"):
        return "https://www.anisearch.de/"
    if(anisearchlang == "English"):
        return "https://www.anisearch.com/"
    if(anisearchlang == "Spanish"):
        return "https://www.anisearch.es/"
    if(anisearchlang == "French"):
        return "https://www.anisearch.fr/"
    if(anisearchlang == "Italian"):
        return "https://www.anisearch.it/"
    if(anisearchlang == "Japanese"):
        return "https://www.anisearch.jp/"

def getFlagLanguage(anisearchlang):
    if(anisearchlang == "German"):
        return "Deutsch"
    if(anisearchlang == "English"):
        return "English"
    if(anisearchlang == "Spanish"):
        return "Español"
    if(anisearchlang == "French"):
        return "Français"
    if(anisearchlang == "Italian"):
        return "Italiana"
    if(anisearchlang == "Japanese"):
        return "日本語"

def getURLfromSearch(query, anisearchlang, page):
    url = getBaseURL(anisearchlang) + "manga/index?text=" + query + "&smode=1&sort=voter&order=desc&quick-search=&char=all&q=true"

    resp = page.goto(url)
    content = page.content()
    new_url = resp.url
    status_code = resp.status

    if("quick-search=" not in new_url):
        printC("Got instant redirect, correct series found")
        return new_url

    if(status_code != 200):
        printC("Status code was " + str(status_code) + ", so skipping...", 'error')
        if(status_code == 403):
            printC(content)
        return ""

    try:
        parser = etree.HTMLParser()
        html_dom = etree.HTML(content, parser)
    except ParserError as e:
        printC(str(e), 'debug')
    try:
        manga_url = html_dom.xpath("//*[@id=\"content-inner\"]/ul[2]/li[1]/a/@href")[0]
        return getBaseURL(anisearchlang) + manga_url
    except:
        return ""

def getMangaMetadata(query, anisearchlang, page):
    printC("Getting metadata for " + str(query))
    status = ""         #done
    summary = ""        #done
    publisher = ""      #done
    #agerating = ""
    genres = []
    tags = []

    data = metadata()

    URL = getURLfromSearch(query, anisearchlang, page)
    if(URL == ""):
        printC("No result found or error occured", 'error')
        return data

    time.sleep(1)

    resp = page.goto(URL)
    content = page.content()
    status_code = resp.status

    if(status_code != 200):
        printC("return code was " + str(status_code) + ", skipping...", 'error')
        return data
    try:
        parser = etree.HTMLParser()
        html_dom = etree.HTML(content, parser)
    except ParserError as e:
        printC(str(e), 'debug')
        return data

    #getLangIndex
    index = 1
    rightIndex = -1
    forcedIndex = "1"
    langRunning = True
    while(langRunning):
        try:
            flag = html_dom.xpath("//*[@id=\"information\"]/div/ul/li[2]/ul/li[" + str(index) + "]/div[1]/img/@title")[0]
            if(flag == getFlagLanguage(anisearchlang)):
                rightIndex = index
                if (anisearchlang == "Japanese"):
                    statusIndex = 3
                    publisherIndex = 6
                else:
                    statusIndex = 2
                    publisherIndex = 5
                    #printC("Found correct Language, index is " + str(rightIndex))
                langRunning = False
                break
            index += 1
        except Exception as e:
            langRunning = False
            statusIndex = 3
            publisherIndex = 6
            break

    if(rightIndex == -1):
        printC("Failed to find set language, using first language as fallback", 'error')
        rightIndex = 1

    rightIndex = str(rightIndex)

    #getStatus
    try:
        status = html_dom.xpath("//*[@id=\"information\"]/div/ul/li[2]/ul/li[" + forcedIndex + "]/div[@class=\"status\"]")[0].itertext()
        status = ''.join(status).split(": ")[1]
    except Exception as e:
        try:
            status = html_dom.xpath("//*[@id=\"information\"]/div/ul/li[2]/ul/li[1]/div[3]")[0].itertext()
            status = ''.join(status).split(": ")[1]
        except Exception as e:
            printC(str(e), 'debug')
            printC("Failed to get status", 'error')

    if(status != ""):
        if(status in runningLang):
            casestatus = "ONGOING"
        elif(status in abandonedLang):
            casestatus = "ABANDONED"
        elif(status in endedLang):
            casestatus = "ENDED"
        else:
            casestatus = "ENDED"
                
            
        data.status = casestatus

    #getTotalBookCount
    try:
        totalBookCount = html_dom.xpath("//*[@id=\"information\"]/div/ul/li[2]/ul/li[" + forcedIndex + "]/div[@class=\"releases\"]")[0].itertext()
        totalBookCount = ''.join(totalBookCount).split(": ")[1].split(" / ")[0].replace("+", "")
        # printC("totalBookCount : "+totalBookCount, 'debug')
    except Exception as e:
        try:
            totalBookCount = html_dom.xpath("//*[@id=\"information\"]/div/ul/li[2]/ul/li[1]/div[@class=\"releases\"]")[0].itertext()
            totalBookCount = ''.join(totalBookCount).split(": ")[1].split(" / ")[0].replace("+", "")
        except Exception as e:
            printC(str(e), 'debug')
            printC("Failed to get totalBookCount", 'error')

    data.totalBookCount = totalBookCount

    #getTotalChaptersCount
    try:
        totalChaptersCount = html_dom.xpath("//*[@id=\"information\"]/div/ul/li[2]/ul/li[" + forcedIndex + "]/div[@class=\"releases\"]")[0].itertext()
        totalChaptersCount = ''.join(totalChaptersCount).split(": ")[1].split(" / ")[1].replace("+", "")
        # printC("totalChaptersCount : "+totalChaptersCount, 'debug')
    except Exception as e:
        try:
            totalChaptersCount = html_dom.xpath("//*[@id=\"information\"]/div/ul/li[2]/ul/li[1]/div[@class=\"releases\"]")[0].itertext()
            totalChaptersCount = ''.join(totalChaptersCount).split(": ")[1].split(" / ")[1].replace("+", "")
        except Exception as e:
            printC(str(e), 'debug')
            printC("Failed to get totalChaptersCount", 'error')

    data.totalChaptersCount = totalChaptersCount

    #getSummary
    try:
        summary = html_dom.xpath("//*[@id=\"description\"]/div/div/div[1]")[0].itertext()
        summary = ''.join(summary)
        for t in tagTexts:
            if(t in summary):
                raise Exception
        for s in noSummaryLang:
            if(s in summary):
                raise Exception
    except Exception as e:
        engsum = ""
        langsum = ""
        sumindex = 1
        noavail = False
        while(True):
            try:
                summary = html_dom.xpath("//*[@id=\"description\"]/div/div/section/div[" + str(sumindex) + "]")[0].itertext()
                summary = ''.join(summary)
                sumlang = html_dom.xpath("//*[@id=\"description\"]/div/div/section/button[" + str(sumindex) + "]")[0].itertext()
                sumlang = ''.join(sumlang)
                for s in noSummaryLang:
                    if (s in summary):
                        printC("No summary available for this language")
                        noavail = True
                        continue
                if (sumlang == getFlagLanguage(anisearchlang) and noavail == False):
                    langsum = summary
                    break
                elif (sumlang == "English"):
                    engsum = summary
                    if(noavail):
                        break
                sumindex += 1
            except Exception as e:
                break

        if(langsum != ""):
            summary = langsum
        else:
            summary = engsum
    if(summary != ""):
        for b in blurbLang:
            if(b in summary.split(":")[0]):
                summary = summary[len(b):]

        summarylist = summary.split(":")[:-1]
        summary = ""
        for s in summarylist:
            summary += s
            summary += ":"

        if(summary[0:1] == ":"):
            summary = summary[1:]

        for sou in summarySourceLang:
            l = len(sou)
            if(summary[len(summary)-l:] == sou):
                summary = summary[:len(summary) - l]
                break

        data.summary = summary.replace("\"", "“")


    #getPublisher
    try:
        publisher = html_dom.xpath("//*[@id=\"information\"]/div/ul/li[2]/ul/li[" + rightIndex + "]/[@class=\"company\"]")[0].itertext()
        publisher = ''.join(publisher)
    except Exception as e:
        try:
            publisher = html_dom.xpath("//*[@id=\"information\"]/div/ul/li[2]/ul/li[1]/div[6]")[0].itertext()
            publisher = ''.join(publisher)
        except Exception as e:
            printC(str(e), 'debug')
            printC("Failed to get publisher", 'error')
    if(publisher != ""):
        publisher = publisher.split(": ")[1]
        data.publisher = publisher

    #Tags & Genres
    i = 1
    running = True
    genrelist = []
    taglist = []
    while(running):
        try:
            tag = html_dom.xpath("//*[@id=\"description\"]/div/div/ul/li[" + str(i) + "]")[0]
            tagstring = ''.join(tag.itertext())


            tagurl = html_dom.xpath("//*[@id=\"description\"]/div/div/ul/li[" + str(i) + "]/a/@href")[0]
            if("/genre/" in tagurl):
                if(tagstring not in genrelist):
                    genrelist.append(tagstring)
            else:
                if(tagstring not in taglist):
                    taglist.append(tagstring)
            i += 1
        except Exception as e:
            #printC(str(e), 'debug')
            running = False

    if(len(genrelist) > 0):
        data.genres = genrelist

    if(len(taglist) > 0):
        data.tags = taglist

    data.isvalid = True
    return data