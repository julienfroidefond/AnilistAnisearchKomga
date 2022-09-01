from pickle import FALSE, TRUE
import requests, json, time, sys, os, signal, webbrowser, math
from datetime import datetime

from io import StringIO, BytesIO

from lxml import etree
from lxml.etree import ParserError

from playwright.sync_api import sync_playwright

resume = "\n\n-----RESUME-----\n"

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

langs = ["German", "English", "Spanish", "French", "Italian", "Japanese"]

def printC(msg, type = 'info'):
    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    global resume
    if(type == "error"):
        resume += bcolors.FAIL+ dt_string + " - [ERROR] : "+msg+bcolors.ENDC+"\n"
        print(bcolors.FAIL+ dt_string + " - [ERROR] : "+msg+bcolors.ENDC)
    elif(type=="success"):
        resume += bcolors.OKGREEN+ dt_string + " - [SUCCESS] : "+msg+bcolors.ENDC+"\n"
        print(bcolors.OKGREEN+ dt_string + " - [SUCCESS] : "+msg+bcolors.ENDC)
    elif(type=="debug"):
        print(bcolors.WARNING+ dt_string + " - [DEBUG] : "+msg+bcolors.ENDC)
    elif(type=="warn"):
        resume += bcolors.WARNING+ dt_string + " - [WARN] : "+msg+bcolors.ENDC+"\n"
        print(bcolors.WARNING+ dt_string + " - [WARN] : "+msg+bcolors.ENDC)
    else:
        print(bcolors.OKBLUE + dt_string + " - [INFO] : "+msg+bcolors.ENDC)

try:
    ENV_URL = os.environ['KOMGAURL']
except:
    ENV_URL = ""
try:
    ENV_EMAIL = os.environ['KOMGAEMAIL']
except:
    ENV_EMAIL = ""
try:
    ENV_PASS = os.environ['KOMGAPASSWORD']
except:
    ENV_PASS = ""
try:
    ENV_LANG = os.environ['LANGUAGE']
except:
    ENV_LANG = ""
try:
    ENV_MANGAS = os.environ['MANGAS']
except:
    ENV_MANGAS = "NONE"
try:
    ENV_LIBS = os.environ['LIBS']
except:
    ENV_LIBS = "NONE"
try:
    ENV_ACTIVATEANILIST = os.environ['ACTIVATEANILIST'] == 'true'
except:
    ENV_ACTIVATEANILIST = False
try:
    ENV_ANILISTUSERNAME = os.environ['ANILISTUSERNAME']
except:
    ENV_ANILISTUSERNAME = "julienfroidefond"
try:
    ENV_ANILISTID = os.environ['ANILISTID']
except:
    ENV_ANILISTID = ""
try:
    ENV_ANILISTSECRET = os.environ['ANILISTSECRET']
except:
    ENV_ANILISTSECRET = ""
try:
    ENV_PROGRESS = os.environ['KEEPPROGRESS']
    if(ENV_PROGRESS.lower() == "true"):
        ENV_PROGRESS = True
    else:
        ENV_PROGRESS = False
except:
    ENV_PROGRESS = False


if (ENV_URL == "" and ENV_EMAIL == "" and ENV_PASS == "" and ENV_LANG == ""):
    try:
        from config import *
    except ImportError:
        printC("Failed to find config.py, does it exist?", 'error')
        sys.exit(1)
elif (ENV_URL != "" and ENV_EMAIL != "" and ENV_PASS != "" and ENV_LANG != ""):
    komgaurl = ENV_URL
    komgaemail = ENV_EMAIL
    komgapassword = ENV_PASS
    anisearchlang = ENV_LANG
    keepProgress = ENV_PROGRESS
    mangas = []
    if(ENV_MANGAS != "NONE"):
        for manga in ENV_MANGAS.split(","):
            if(manga[:1] == " "):
                manga = manga[1:]
            mangas.append(manga)
    libraries = []
    if(ENV_LIBS != "NONE"):
        for lib in ENV_LIBS.split(","):
            if(lib[:1] == " "):
                lib = lib[1:]
            libraries.append(lib)
else:
    printC("Looks like either you are trying to set the configuration using environment variables or you are using docker.")
    if(ENV_URL == ""):
        printC("Missing Komga URL")
    if(ENV_EMAIL == ""):
        printC("Missing Komga Email")
    if(ENV_PASS == ""):
        printC("Missing Komga Password")
    if(ENV_LANG == ""):
        printC("Missing Anisearch language")
    sys.exit(1)

if(anisearchlang not in langs):
    printC("Invalid language, select one listed the README", 'error')
    sys.exit(1)

activateAnilistSync = False
if(ENV_ACTIVATEANILIST == True and ENV_ANILISTID != "" and ENV_ANILISTSECRET != '' and ENV_ANILISTUSERNAME != ''):
    activateAnilistSync=True
    printC("Synchronization Anilist is activated")
else:
    printC("No synchronization Anilist. Please check environment variables.", "warn")

def getBaseURL():
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

def getFlagLanguage():
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


summarySourceLang = [" Quelle: ", " Quelle:", "Quelle:", " Source: ", " Source:", "Source:"]
runningLang = ["Laufend", "Ongoing", "Corriente", "En cours", "In corso", "放送", "放送（連載）中"]
abandonedLang = ["Abgebrochen", "Aborted", "Cancelado", "Annulé", "Abbandonato", "打ち切り"]
endedLang = ["Abgeschlossen", "Completed", "Completado", "Terminé", "Completato", "完結"]
tagTexts = ["Hauptgenres", "Main genres", "Género principal", "Principaux genres", "Generi principali", "メインジャンル"]
noSummaryLang = ["Damit hilfst Du der gesamten deutschsprachigen Anime und Manga-Community", "We’re looking forward to your contributions", "Con esto ayudas a toda la comunidad de Anime y Manga", "Nous attendons avec impatience tes contributions", "Non vediamo l’ora di ricevere i tuoi contributi", "皆様からのご投稿をお待ちしております"]
blurbLang = ["Klappentext", "Blurb", "Texto de presentación", "Texte du rabat", "Testo della bandella"]


class metadata:
    def __init__(self):
            self.status = ""
            self.summary = ""
            self.publisher = ""
#            self.agerating = ""
            self.genres = []
            self.tags = []
            self.isvalid = False

def getURLfromSearch(query):
    url = getBaseURL() + "manga/index?text=" + query + "&smode=1&sort=voter&order=desc&quick-search=&char=all&q=true"


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
        return getBaseURL() + manga_url
    except:
        return ""

#out = open("out.txt", "w", encoding='utf-8')
#out.write(tree.tostring(tree.getroot()).content.decode(sys.stdout.encoding, errors='replace'))
#out.close()

#printC(getURLfromSearch("adekan"))

# Reading datas
datas={"series":[]}
with open('datas.json') as json_file:
    datas = json.load(json_file)
    if("series" not in datas.keys()):
        datas={"series":[]}

def getMangaMetadata(query):
    printC("Getting metadata for " + str(query))
    status = ""         #done
    summary = ""        #done
    publisher = ""      #done
    #agerating = ""
    genres = []
    tags = []

    data = metadata()

    URL = getURLfromSearch(query)
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
            if(flag == getFlagLanguage()):
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
                if (sumlang == getFlagLanguage() and noavail == False):
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

def anilistGet(name, seriesID):
    printC("get and write JSON anilist for "+name)
    currentSerie = None
    for serieData in datas["series"]:
        if(serieData["name"]==name):
            currentSerie = serieData
    if currentSerie is None:
        datas["series"].append({"name":name, "komgaId":seriesID})

    for serieData in datas["series"]:
        if(serieData["name"]==name):
            currentSerie = serieData
            
    try:
        if("anilistInfo" not in currentSerie.keys()):
            query = '''
            query ($search: String) {
                Page {
                    media (search: $search, type: MANGA, format: MANGA, , genre_not_in: "Hentai") {
                        id
                        title {
                            romaji
                            english
                            native
                            userPreferred
                        }
                        volumes
                        chapters
                    }
                }
            }
            '''
            variables = {
                'search': currentSerie["name"]
            }
            url = 'https://graphql.anilist.co'
            printC("Getting info from anilist")
            response = requests.post(url, json={'query': query, 'variables': variables})
            resData = json.loads(response.text)
            if "data" in resData.keys():
                if(len(resData["data"]["Page"]["media"]) > 0):
                    currentSerie["anilistInfo"] = resData["data"]["Page"]["media"][0]
                    printC("Successfully get from anilist for " + currentSerie["name"], 'success')
                    logStatus(datas, name, "anilist get", "Manga found all ok", True)
                    return currentSerie["anilistInfo"]
                else:
                    # printC(json.dumps(resData,skipkeys = True),'debug')
                    # printC(json.dumps(query,skipkeys = True),'debug')
                    # printC(json.dumps(variables,skipkeys = True),'debug')
                    printC("Manga not found on anilist : "+name, "error")
                    logStatus(datas, name, "anilist get", "Manga not found on anilist", True)
            else:
                printC(resData,"debug")
        else:
            logStatus(datas, name, "anilist get", "Manga already in local", True)
            return currentSerie["anilistInfo"]

    except Exception as e:
        printC(str(e), "debug")
        printC("Failed to get from anilist", 'error')
        return {"id":0}

def aniListConnect():
    accessToken=''
    if("anilistAccessToken" not in datas.keys()):
        input("Now we will invite you to generate a code for doing update in your Anilit account (Press Enter)")
        webbrowser.open("https://anilist.co/api/v2/oauth/authorize?client_id="+ENV_ANILISTID+"&redirect_uri=https://anilist.co/api/v2/oauth/pin&response_type=code")
        code = input("Paste here : \n")
        datas["anilistUserCode"] = code
        response =requests.post("https://anilist.co/api/v2/oauth/token", headers = {
            "Content-Type": "application/json",
            'Accept': 'application/json'
            }, json={
            'grant_type': 'authorization_code',
            'client_id': ENV_ANILISTID,
            'client_secret': ENV_ANILISTSECRET,
            'redirect_uri': 'https://anilist.co/api/v2/oauth/pin',
            'code': code
        })
        print(json.loads(response.text))
        accessToken = json.loads(response.text)['access_token']
        printC("Successfully get a token from anilist for user", "success")
        datas["anilistAccessToken"] = accessToken
    else:
        accessToken = datas["anilistAccessToken"]
    return accessToken

def getUserCurrentLists():
    query = '''
    query ($userName: String) {
        Page {
            mediaList(userName: $userName) {
            mediaId
            status
            progressVolumes
            }
        }
    }
    '''
    variables = {
        'userName': ENV_ANILISTUSERNAME
    }
    url = 'https://graphql.anilist.co'
    printC("Getting user's lists from anilist for " + ENV_ANILISTUSERNAME)
    response = requests.post(url, json={'query': query, 'variables': variables})
    resData = json.loads(response.text)
    return resData['data']['Page']['mediaList']
 
def anilistAdd(anilistData, name, series, userMediaList, accessToken, md):
    booksReadCount = series['booksReadCount']
    totalBookCount = series['metadata']['totalBookCount']
    totalChaptersCount = md["totalChaptersCount"]

    anilistId=anilistData["id"]
    if anilistId != 0:
        currentUserMedia = None
        for userMedia in userMediaList:
            if(userMedia['mediaId'] == anilistId):
                currentUserMedia = userMedia
        
        status="PLANNING"
        if booksReadCount == 0 or totalBookCount is None:
            status="PLANNING"
        elif booksReadCount == totalBookCount:
            status="COMPLETED"
        elif booksReadCount > 0:
            status="CURRENT"

        progressChapters=0
        if(totalChaptersCount is not None and totalBookCount is not None):
            if(status == "COMPLETED"):
                progressChapters = int(totalChaptersCount)
            else:
                chapByVol = int(totalBookCount) / int(totalChaptersCount)
                progressChapters= math.ceil(currentUserMedia['progressVolumes'] / chapByVol)

        hasToUpdate = True
        if(currentUserMedia):
            if(currentUserMedia['status'] != "PLANNING" and currentUserMedia['status'] != "COMPLETED" and currentUserMedia['status'] != "CURRENT") :
                printC("Not updating anilist : preserving status : " + currentUserMedia['status'])
                logStatus(datas, name, "anilist push", "Not updating anilist : preserving status : " + currentUserMedia['status'], True)
                hasToUpdate = False
            if(currentUserMedia['status'] == status and booksReadCount <= currentUserMedia['progressVolumes']):
                printC("Not updating anilist : preserving volumes count : " + str(currentUserMedia['progressVolumes']) + " VS LOCAL : " +str(booksReadCount))
                logStatus(datas, name, "anilist push", "Not updating anilist : preserving volumes count : " + str(currentUserMedia['progressVolumes']) + " VS LOCAL : " +str(booksReadCount), True)
                hasToUpdate = False


        if(hasToUpdate == True):
            query = '''
            mutation ($mediaId: Int, $status: MediaListStatus, $progressVolumes: Int, $progress: Int) {
                SaveMediaListEntry (mediaId: $mediaId, status: $status, progressVolumes: $progressVolumes, progress: $progress) {
                    id
                    status
                }
            }
            ''';
            variables = {
                "mediaId" : anilistId,
                "status" : status,
                "progress" : progressChapters,
                "progressVolumes" : booksReadCount
            };
            res = requests.post("https://graphql.anilist.co", headers = {
                "Content-Type": "application/json",
                'Accept': 'application/json',
                "Authorization": "Bearer " + accessToken
                }, json = {
                    'query' : query,
                    'variables' :variables
            })
            jsonRes = json.loads(res.text)
            if("data" in jsonRes.keys()):
                printC("Successfully anilist synchronized " + name + " in status " + status + " with " + str(booksReadCount) + " volumes and " + str(progressChapters) + " chapters", "success")
                logStatus(datas, name, "anilist push success", "synchronized  in status " + status + " with " + str(booksReadCount) + " volumes and " + str(progressChapters), False)
            else:
                printC("Error when uploading on anilist : "+jsonRes, "error")
                logStatus(datas, name, "anilist push", "Error " + jsonRes, True)

def logStatus(datas, name, type, status, oneTime):
    currentSerie = None
    for serieData in datas["series"]:
        if(serieData["name"]==name):
            currentSerie = serieData
    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    states = {}
    if("status" in currentSerie.keys()):
        states=currentSerie["status"]

    states[type] = "[" + dt_string + "] : " + status
    currentSerie["status"] = states

def writeDatasJSON():
    with open('datas.json', 'w') as outfile:
        json.dump(datas, outfile, indent=3)
        printC("Successfully write to JSON !", 'success')

def handler(signum, frame):
    printC("Quittind app by SIGINT; writing")
    print(resume)
    writeDatasJSON()
    sys.exit(1)

signal.signal(signal.SIGINT, handler)

p_context = sync_playwright()
p = p_context.__enter__()
browser = p.chromium.launch()
page = browser.new_page()
page.goto(getBaseURL())


printC("Using user " + komgaemail)
printC("Using server " + komgaurl)
if activateAnilistSync:
    printC("Using anilist client id " + ENV_ANILISTID)
    printC("Using anilist secret id " + ENV_ANILISTSECRET)
    printC("Using anilist user " + ENV_ANILISTUSERNAME)


libreq = requests.get(komgaurl + '/api/v1/libraries', auth = (komgaemail, komgapassword))
json_lib = json.loads(libreq.text)

x = requests.get(komgaurl + '/api/v1/series?size=50000', auth = (komgaemail, komgapassword))

json_string = json.loads(x.text)

seriesnum = 0
try:
    expected = json_string['numberOfElements']
except:
    printC("Failed to get list of mangas, are the login infos correct?", 'error')
    sys.exit(1)

printC("Series to do: " + str(expected))

class failedtries():
    def __init__(self, id, name):
        self.id = id
        self.name = name

failed = []

progressfilename = "mangas.progress"

def addMangaProgress(seriesID):
    if(keepProgress == False):
        return
    progfile = open(progressfilename, "a+")
    progfile.write(str(seriesID) + "\n")
    progfile.close()


progresslist = []
if(keepProgress):
    printC("Loading list of successfully updated mangas")
    try:
        with open(progressfilename) as file:
            progresslist = [line.rstrip() for line in file]
    except:
        printC("Failed to load list of mangas", 'error')

userMediaList = []
if activateAnilistSync:
    accessToken = aniListConnect()
    userMediaList = getUserCurrentLists()

forceUpdateFull = False

failedfile = open("failed.txt", "w")
for series in json_string['content']:
    seriesID = series['id']
    name = series['metadata']['title']

    currentSerie = None
    for serieData in datas["series"]:
        if(serieData["name"]==name):
            currentSerie = serieData

    if currentSerie is not None :
        skipUpdate = False
        skipSync = False
        seriesnum += 1
        isFinished = False
        if (series['metadata']['statusLock'] == True and series['metadata']['status'] == 'ENDED'):
            isFinished = True
        if "metadatas" not in currentSerie :
            printC("No metadatas in datas; we force update for " + name, "error")
            isFinished = False
        if(len(mangas) > 0):
            if(series['name'] not in mangas):
                skipUpdate = True
                skipSync = True

        if(len(libraries) > 0):
            libraryId = series['libraryId']
            currentLib = ""
            for libKom in json_lib:
                if libKom['id'] == libraryId:
                    currentLib = libKom['name']
            if(currentLib not in libraries):
                # printC("ignoring "+str(name)+" not in right lib", 'warn')
                skipUpdate = True
                skipSync = True
        
        if activateAnilistSync and skipSync is False:
            anilistData = anilistGet(name, seriesID)

        if (isFinished == True and forceUpdateFull is False):
            printC("Ignoring "+str(name)+" : series terminated and already synchronized", 'warn')
            skipUpdate = True

        printC("Number: " + str(seriesnum) + "/" + str(expected))
        
        if(str(seriesID) in progresslist):
            printC("Manga " + str(name) + " was already updated, skipping...")
            skipUpdate = True

        if(skipUpdate is False):
            printC("Updating: " + str(name))
            md = getMangaMetadata(name)
            if(md.isvalid == False):
                printC("----------------------------------------------------")
                printC("Failed to update " + str(name) + ", trying again at the end", 'error')
                printC("----------------------------------------------------")
                fail = failedtries(seriesID, name)
                failed.append(fail)
                failedfile.write(str(seriesID))
                failedfile.write(name)
                time.sleep(10)
                continue
            jsonToPush = {
                "language": "fr",
                "languageLock": True,
                "status": md.status,
                "statusLock": True,
                "summary": md.summary,
                "summaryLock": True,
                "publisher": md.publisher,
                "publisherLock": True,
                "genres": md.genres,
                "genresLock": True,
                "tags": md.tags,
                "tagsLock": True,
                "totalBookCount": md.totalBookCount,
                "totalBookCountLock": True
            }
            currentSerie["metadatas"] = {
                "status": md.status,
                "totalBookCount": md.totalBookCount,
                "totalChaptersCount": md.totalChaptersCount,
            }
            pushdata = json.dumps(jsonToPush, ensure_ascii=False).replace("\n", "").replace("\r", "")
            headers = {'Content-Type': 'application/json', 'accept': '*/*'}
            patch = requests.patch(komgaurl + "/api/v1/series/" + seriesID + "/metadata", data=str.encode(pushdata), auth = (komgaemail, komgapassword), headers=headers)
            if(patch.status_code == 204):
                printC("----------------------------------------------------")
                printC("Successfully updated " + str(name), 'success')
                printC("----------------------------------------------------")
                addMangaProgress(seriesID)
                time.sleep(10)
            else:
                try:
                    printC("----------------------------------------------------")
                    printC(pushdata, "debug")
                    printC("Failed to update " + str(name), 'error')
                    printC(patch, 'error')
                    printC(patch.text, 'error')
                    printC("----------------------------------------------------")
                    failedfile.write(str(seriesID))
                    failedfile.write(name)
                    fail = failedtries(seriesID, name)
                    failed.append(fail)
                except:
                    pass
        
        if activateAnilistSync and skipSync is False:
            anilistAdd(anilistData, name, series, userMediaList, accessToken, currentSerie["metadatas"])

writeDatasJSON()
print(resume)

failedfile.close()



# for f in failed:
#     md = getMangaMetadata(f.name)
#     if (md.isvalid == False):
#         printC("----------------------------------------------------")
#         printC("Failed again to update " + str(f.name) + ", not trying again")
#         printC("----------------------------------------------------")
#         time.sleep(10)
#         continue
#     jsondata = """{
#       "status": %s,
#       "statusLock": true,
#       "summary": "%s",
#       "summaryLock": true,
#       "publisher": "%s",
#       "publisherLock": true,
#       "genres": %s,
#       "genresLock": true,
#       "tags": %s,
#       "tagsLock": true
#     }""" % (md.status, md.summary.replace('\n', '\\n'), md.publisher, md.genres, md.tags)
#     pushdata = jsondata.replace("\n", "").replace("{  \\\"status\\\": ", "{\\\"status\\\":").replace(",  \\\"statusLock\\\": ", ",\\\"statusLock\\\":").replace(",  \\\"summary\\\": ", ",\\\"summary\\\":").replace(",  \\\"summaryLock\\\": ", ",\\\"summaryLock\\\":").replace("\n", "").replace("\r", "")
#     printC(pushdata)
#     headers = {'Content-Type': 'application/json', 'accept': '*/*'}
#     patch = requests.patch(komgaurl + "/api/v1/series/" + seriesID + "/metadata", data=str.encode(pushdata), auth = (komgaemail, komgapassword), headers=headers)
#     if(patch.status_code == 204):
#         printC("++++++++++++++++++++++++++++++++++++++++++++++++++++")
#         printC("Successfully updated " + str(f.name), 'success')
#         printC("++++++++++++++++++++++++++++++++++++++++++++++++++++")
#         addMangaProgress(seriesID)
#         time.sleep(10)
#     else:
#         printC("----------------------------------------------------")
#         printC("Failed again to update " + str(f.name) + ", not trying again")
#         printC("----------------------------------------------------")
#         addMangaProgress(seriesID)
#         time.sleep(10)
#         continue