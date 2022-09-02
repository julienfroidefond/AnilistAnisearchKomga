import requests, json, time, sys, os, signal

from playwright.sync_api import sync_playwright

from utils import *
from anilist import *
from anisearch import *

resume = "\n\n-----RESUME-----\n"
coucou = True

langs = ["German", "English", "Spanish", "French", "Italian", "Japanese"]

# Environment and variables
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
        resume += printC("Failed to find config.py, does it exist?", 'error')
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
    resume += printC("Looks like either you are trying to set the configuration using environment variables or you are using docker.")
    if(ENV_URL == ""):
        resume += printC("Missing Komga URL")
    if(ENV_EMAIL == ""):
        resume += printC("Missing Komga Email")
    if(ENV_PASS == ""):
        resume += printC("Missing Komga Password")
    if(ENV_LANG == ""):
        resume += printC("Missing Anisearch language")
    sys.exit(1)
# --- end Environment and variables

if(anisearchlang not in langs):
    resume += printC("Invalid language, select one listed the README", 'error')
    sys.exit(1)

activateAnilistSync = False
if(ENV_ACTIVATEANILIST == True and ENV_ANILISTID != "" and ENV_ANILISTSECRET != '' and ENV_ANILISTUSERNAME != ''):
    activateAnilistSync=True
    resume += printC("Synchronization Anilist is activated")
else:
    resume += printC("No synchronization Anilist. Please check environment variables.", "warn")

# Reading datas
datas={"series":[]}
try:
    with open('datas.json') as json_file:
        datas = json.load(json_file)
        if("series" not in datas.keys()):
            datas={"series":[]}
except:
    datas={"series":[]}

def writeDatasJSON():
    with open('datas.json', 'w') as outfile:
        json.dump(datas, outfile, indent=3)
        printC("Successfully write to JSON !", 'success')

def handler(signum, frame):
    global resume
    resume += printC("Quittind app by SIGINT; writing")
    print(resume)
    writeDatasJSON()
    sys.exit(1)

signal.signal(signal.SIGINT, handler)

resume += printC("Using user " + komgaemail)
resume += printC("Using server " + komgaurl)
if activateAnilistSync:
    resume += printC("Using anilist client id " + ENV_ANILISTID)
    resume += printC("Using anilist secret id " + ENV_ANILISTSECRET)
    resume += printC("Using anilist user " + ENV_ANILISTUSERNAME)


libreq = requests.get(komgaurl + '/api/v1/libraries', auth = (komgaemail, komgapassword))
json_lib = json.loads(libreq.text)

x = requests.get(komgaurl + '/api/v1/series?size=50000', auth = (komgaemail, komgapassword))

json_string = json.loads(x.text)

seriesnum = 0
try:
    expected = json_string['numberOfElements']
except:
    resume += printC("Failed to get list of mangas, are the login infos correct?", 'error')
    sys.exit(1)

resume += printC("Series to do: " + str(expected))

progressfilename = "mangas.progress"

def addMangaProgress(seriesID):
    if(keepProgress == False):
        return
    progfile = open(progressfilename, "a+")
    progfile.write(str(seriesID) + "\n")
    progfile.close()


progresslist = []
if(keepProgress):
    resume += printC("Loading list of successfully updated mangas")
    try:
        with open(progressfilename) as file:
            progresslist = [line.rstrip() for line in file]
    except:
        resume += printC("Failed to load list of mangas", 'error')

userMediaList = []
if activateAnilistSync:
    accessToken = aniListConnect(datas)
    userMediaList = getUserCurrentLists(ENV_ANILISTUSERNAME, datas)

forceUpdateFull = False

# Have to do the page object before 
p_context = sync_playwright()
p = p_context.__enter__()
browser = p.chromium.launch()
page = browser.new_page()
page.goto(getBaseURL(anisearchlang))

for series in json_string['content']:
    seriesID = series['id']
    name = series['metadata']['title']

    # Get serie in datas.json
    currentSerie = None
    for serieData in datas["series"]:
        if(serieData["name"]==name):
            currentSerie = serieData

    skipUpdate = False
    skipSync = False
    seriesnum += 1
    isFinished = False
    if (series['metadata']['statusLock'] == True and series['metadata']['status'] == 'ENDED'):
        isFinished = True
    if currentSerie is not None :
        if "metadatas" not in currentSerie :
            resume += printC("No metadatas in datas; we force update for " + name, "error")
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
            # resume += printC("ignoring "+str(name)+" not in right lib", 'warn')
            skipUpdate = True
            skipSync = True
    
    if activateAnilistSync and skipSync is False:
        anilistData = anilistGet(name, seriesID, datas)

    if (isFinished == True and forceUpdateFull is False):
        resume += printC("Ignoring "+str(name)+" : series terminated and already synchronized", 'warn')
        skipUpdate = True

    resume += printC("Number: " + str(seriesnum) + "/" + str(expected))
    
    if(str(seriesID) in progresslist):
        resume += printC("Manga " + str(name) + " was already updated, skipping...")
        skipUpdate = True

    if(skipUpdate is False):
        resume += printC("Updating: " + str(name))
        md = getMangaMetadata(name, anisearchlang, page)
        if(md.isvalid == False):
            resume += printC("----------------------------------------------------")
            resume += printC("Failed to update " + str(name) + ", trying again at the end", 'error')
            resume += printC("----------------------------------------------------")
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
            resume += printC("----------------------------------------------------")
            resume += printC("Successfully updated " + str(name), 'success')
            resume += printC("----------------------------------------------------")
            addMangaProgress(seriesID)
            time.sleep(10)
        else:
            try:
                resume += printC("----------------------------------------------------")
                resume += printC(pushdata, "debug")
                resume += printC("Failed to update " + str(name), 'error')
                resume += printC(patch, 'error')
                resume += printC(patch.text, 'error')
                resume += printC("----------------------------------------------------")
            except:
                pass
            
    if currentSerie is not None :
        if activateAnilistSync and skipSync is False:
            anilistAdd(anilistData, name, series, userMediaList, accessToken, currentSerie["metadatas"], datas)

writeDatasJSON()
print(resume)