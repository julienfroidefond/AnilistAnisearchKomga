import requests, json, time, sys, signal

from playwright.sync_api import sync_playwright

from utils import *
from anilist import *
from anisearch import *

komgaurl, komgaemail, komgapassword, anisearchlang, mangas, activateAnilistSync, anilistClientId, anilistSecret, anilistUsername, libraries = getEnvVars()

printC("Using user " + komgaemail)
printC("Using server " + komgaurl)
if activateAnilistSync:
    printC("Using anilist client id " + anilistClientId)
    printC("Using anilist secret id " + anilistSecret)
    printC("Using anilist user " + anilistUsername)

datas = getDatasFromFile()

def handler(signum, frame):
    printC("Quittind app by SIGINT; writing")
    writeDatasJSON(datas)
    sys.exit(1)
signal.signal(signal.SIGINT, handler)

# --------- Komga get
libreq = requests.get(komgaurl + '/api/v1/libraries', auth = (komgaemail, komgapassword))
json_lib = json.loads(libreq.text)
x = requests.get(komgaurl + '/api/v1/series?size=50000', auth = (komgaemail, komgapassword))
json_string = json.loads(x.text)

try:
    expected = json_string['numberOfElements']
except:
    printC("Failed to get list of mangas, are the login infos correct?", 'error')
    sys.exit(1)

printC("Series to do: " + str(expected))

# --------- Getting anilist lists of the user
userMediaList = []
if activateAnilistSync and anilistUsername != "":
    accessToken = aniListConnect(datas.get("anilistAccessToken", ""), anilistClientId, anilistSecret)
    datas["anilistAccessToken"] = accessToken
    userMediaList = getUserCurrentLists(anilistUsername)
    userMediaList = userMediaList + getUserCurrentCLists(anilistUsername)

forceUpdateFull = False

# --------- Have to do the page object before 
p_context = sync_playwright()
p = p_context.__enter__()
browser = p.chromium.launch()
page = browser.new_page()
page.goto(getBaseURL(anisearchlang))

seriesnum = 0
for series in json_string['content'][::-1]:
    seriesID = series['id']
    name = series['metadata']['title']
    if isInLib(libraries, series, json_lib) is True:
        
        currentSerie = getSerieByName(datas, name)

        skipUpdate, skipSync = getSkipStatuses(series, name, mangas, forceUpdateFull, currentSerie)

        seriesnum += 1
        printC("Number: " + str(seriesnum) + "/" + str(expected))

        # --------- get from anilist
        anilistData = anilistGet(currentSerie, forceUpdateFull)
        currentSerie["anilistInfo"] = anilistData
        
        if(skipUpdate is False):
            printC("Updating: " + str(name)) 
            
            # --------- map anilist <> Komga
            jsonToPush = mapAnilistToKomga(anilistData)

            # --------- Get from anisearch
            md = getMangaMetadata(name, anisearchlang, page)
            if(md.isvalid == False):
                printC("----------------------------------------------------")
                printC("Failed to update from anisearch " + str(name), 'error')
                printC("----------------------------------------------------")
                continue
            jsonToPush = mapAniSearchToKomga(md, jsonToPush) 
            
            currentSerie["metadatas"] = {
                "status": md.status,
                "totalBookCount": md.totalBookCount,
                "totalChaptersCount": md.totalChaptersCount
            }

            # --------- Update Komga 
            pushdata = json.dumps(jsonToPush, ensure_ascii=False).replace("\n", "").replace("\r", "")
            headers = {'Content-Type': 'application/json', 'accept': '*/*'}
            patch = requests.patch(komgaurl + "/api/v1/series/" + seriesID + "/metadata", data=str.encode(pushdata), auth = (komgaemail, komgapassword), headers=headers)
            if(patch.status_code == 204):
                printC("----------------------------------------------------")
                printC("Successfully updated " + str(name), 'success')
                printC("----------------------------------------------------")
                time.sleep(10)
            else:
                try:
                    printC("----------------------------------------------------")
                    printC(pushdata, "debug")
                    printC("Failed to update " + str(name), 'error')
                    printC(patch, 'error')
                    printC(patch.text, 'error')
                    printC("----------------------------------------------------")
                except:
                    pass

        # --------- Actualize nb book read
        currentSerie["metadatas"]["booksReadCount"] = str(series['booksReadCount'])
        # --------- Save to anilist user lists states
        if currentSerie is not None:
            if activateAnilistSync and skipSync is False:
                anilistAdd(userMediaList, accessToken, currentSerie)

writeDatasJSON(datas)
