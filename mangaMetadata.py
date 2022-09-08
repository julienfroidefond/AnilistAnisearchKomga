import requests, json, time, sys, signal

from playwright.sync_api import sync_playwright

from utils import *
from anilist import *
from anisearch import *

resume = "\n\n-----RESUME-----\n"

def printR(msg, type = 'info'):
    global resume
    resume += printC(msg, type)

komgaurl, komgaemail, komgapassword, anisearchlang, keepProgress, mangas, activateAnilistSync, anilistClientId, anilistSecret, anilistUsername, libraries = getEnvVars()

printR("Using user " + komgaemail)
printR("Using server " + komgaurl)
if activateAnilistSync:
    printR("Using anilist client id " + anilistClientId)
    printR("Using anilist secret id " + anilistSecret)
    printR("Using anilist user " + anilistUsername)

datas = getDatasFromFile()

def handler(signum, frame):
    global resume
    printR("Quittind app by SIGINT; writing")
    print(resume)
    writeDatasJSON(datas)
    sys.exit(1)
signal.signal(signal.SIGINT, handler)

libreq = requests.get(komgaurl + '/api/v1/libraries', auth = (komgaemail, komgapassword))
json_lib = json.loads(libreq.text)

x = requests.get(komgaurl + '/api/v1/series?size=50000', auth = (komgaemail, komgapassword))

json_string = json.loads(x.text)

seriesnum = 0
try:
    expected = json_string['numberOfElements']
except:
    printR("Failed to get list of mangas, are the login infos correct?", 'error')
    sys.exit(1)

printR("Series to do: " + str(expected))

progressfilename = "mangas.progress"

def addMangaProgress(seriesID):
    if(keepProgress == False):
        return
    progfile = open(progressfilename, "a+")
    progfile.write(str(seriesID) + "\n")
    progfile.close()


progresslist = []
if(keepProgress):
    printR("Loading list of successfully updated mangas")
    try:
        with open(progressfilename) as file:
            progresslist = [line.rstrip() for line in file]
    except:
        printR("Failed to load list of mangas", 'error')

userMediaList = []
if activateAnilistSync:
    accessToken = aniListConnect(datas)
    userMediaList = getUserCurrentLists(anilistUsername, datas)

forceUpdateFull = False

# --------- Have to do the page object before 
p_context = sync_playwright()
p = p_context.__enter__()
browser = p.chromium.launch()
page = browser.new_page()
page.goto(getBaseURL(anisearchlang))

for series in json_string['content']:
    seriesID = series['id']
    name = series['metadata']['title']

    currentSerie = getSerieByName(datas, name)

    skipUpdate = False
    skipSync = False
    seriesnum += 1
    isFinished = False
    if (series['metadata']['statusLock'] == True and series['metadata']['status'] == 'ENDED'):
        isFinished = True
    if currentSerie is not None :
        if "metadatas" not in currentSerie :
            printR("No metadatas in datas; we force update for " + name, "error")
            isFinished = False
    else:
        currentSerie={}
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
            # printR("ignoring "+str(name)+" not in right lib", 'warn')
            skipUpdate = True
            skipSync = True

    if (isFinished == True and forceUpdateFull is False):
        printR("Ignoring "+str(name)+" : series terminated and already synchronized", 'warn')
        skipUpdate = True

    printR("Number: " + str(seriesnum) + "/" + str(expected))
    
    if(str(seriesID) in progresslist):
        printR("Manga " + str(name) + " was already updated, skipping...")
        skipUpdate = True

    anilistData = anilistGet(name, seriesID, datas, forceUpdateFull)
    
    if(skipUpdate is False):
        printR("Updating: " + str(name)) 
        
        jsonToPush = mapAnilistToKomga(anilistData)

        md = getMangaMetadata(name, anisearchlang, page)
        if(md.isvalid == False):
            printR("----------------------------------------------------")
            printR("Failed to update from anisearch " + str(name), 'error')
            printR("----------------------------------------------------")
            continue
        jsonToPush = mapAniSearchToKomga(md, jsonToPush) 
        
        currentSerie["metadatas"] = {
            "status": md.status,
            "totalBookCount": md.totalBookCount,
            "totalChaptersCount": md.totalChaptersCount,
        }
        pushdata = json.dumps(jsonToPush, ensure_ascii=False).replace("\n", "").replace("\r", "")
        headers = {'Content-Type': 'application/json', 'accept': '*/*'}
        patch = requests.patch(komgaurl + "/api/v1/series/" + seriesID + "/metadata", data=str.encode(pushdata), auth = (komgaemail, komgapassword), headers=headers)
        if(patch.status_code == 204):
            printR("----------------------------------------------------")
            printR("Successfully updated " + str(name), 'success')
            printR("----------------------------------------------------")
            addMangaProgress(seriesID)
            time.sleep(10)
        else:
            try:
                printR("----------------------------------------------------")
                printR(pushdata, "debug")
                printR("Failed to update " + str(name), 'error')
                printR(patch, 'error')
                printR(patch.text, 'error')
                printR("----------------------------------------------------")
            except:
                pass
            
    if currentSerie is not None :
        if activateAnilistSync and skipSync is False and "metadatas" in currentSerie.keys():
            anilistAdd(anilistData["id"], name, series, userMediaList, accessToken, currentSerie["metadatas"], datas)

writeDatasJSON(datas)
print(resume)
