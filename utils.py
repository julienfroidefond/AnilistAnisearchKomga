import sys, json, os
from datetime import datetime

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

onlyResume = False
if(len(sys.argv)>1):
    if(sys.argv[1] == "onlyResume"):
        onlyResume=True

def printC(msg, type = 'info'):
    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    resume=""
    printMsg = ""
    if(type == "error"):
        printMsg = bcolors.FAIL+ dt_string + " - [ERROR] : "+msg+bcolors.ENDC
        resume = printMsg
    elif(type=="success"):
        printMsg = bcolors.OKGREEN+ dt_string + " - [SUCCESS] : "+msg+bcolors.ENDC
        resume = printMsg
    elif(type=="debug"):
        printMsg = bcolors.WARNING+ dt_string + " - [DEBUG] : "+msg+bcolors.ENDC
    elif(type=="warn"):
        printMsg = bcolors.WARNING+ dt_string + " - [WARN] : "+msg+bcolors.ENDC
        resume = printMsg
    else:
        printMsg=bcolors.OKBLUE + dt_string + " - [INFO] : "+msg+bcolors.ENDC

    if(onlyResume is False):
        print(printMsg)
    else:
        if(resume != ""):
            print(resume)

def logStatus(currentSerie, type, status, oneTime):
    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    states = {}
    if("status" in currentSerie.keys()):
        states=currentSerie["status"]

    states[type] = "[" + dt_string + "] : " + status
    currentSerie["status"] = states

def getSerieByName(datas, name):
    serie = None
    for serieData in datas["series"]:
        if(serieData["name"] == name):
            serie = serieData
    if serie is None:
        s={"name": name}
        datas["series"].append(s)
        return s
    else:
        return serie

def setSerieByName(datas, name, serie):
    serie = None
    for serieData in datas["series"]:
        if(serieData["name"] == name):
            serieData["name"] = serie

def writeDatasJSON(datas):
    with open('datas.json', 'w') as outfile:
        json.dump(datas, outfile, indent=3)
        printC("Successfully write to JSON !", 'success')

def getDatasFromFile():
    datas={"series":[]}
    try:
        with open('datas.json') as json_file:
            datas = json.load(json_file)
            if("series" not in datas.keys()):
                datas={"series":[]}
    except:
        datas={"series":[]}
    
    return datas

def getEnvVars():
    langs = ["German", "English", "Spanish", "French", "Italian", "Japanese"]

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

    if (ENV_URL == "" and ENV_EMAIL == "" and ENV_PASS == "" and ENV_LANG == ""):
        printC("Failed to find config.py, does it exist?", 'error')
        sys.exit(1)
    elif (ENV_URL != "" and ENV_EMAIL != "" and ENV_PASS != "" and ENV_LANG != ""):
        komgaurl = ENV_URL
        komgaemail = ENV_EMAIL
        komgapassword = ENV_PASS
        anisearchlang = ENV_LANG
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
    # --- end Environment and variables

    if(anisearchlang not in langs):
        printC("Invalid language, select one listed the README", 'error')
        sys.exit(1)

    activateAnilistSync = False
    if(ENV_ACTIVATEANILIST == True and ENV_ANILISTID != "" and ENV_ANILISTSECRET != '' and ENV_ANILISTUSERNAME != ''):
        activateAnilistSync=True
        printC("Synchronization Anilist is activated")
    else:
        printC("No synchronization Anilist. Please check environment variables.", "warn")

    anilistClientId = ENV_ANILISTID
    anilistSecret = ENV_ANILISTSECRET
    anilistUsername = ENV_ANILISTUSERNAME

    
    return komgaurl, komgaemail, komgapassword, anisearchlang, mangas, activateAnilistSync, anilistClientId, anilistSecret, anilistUsername, libraries

def isInLib(libraries, series, json_lib):
    if(len(libraries) > 0):
        libraryId = series['libraryId']
        currentLib = ""
        for libKom in json_lib:
            if libKom['id'] == libraryId:
                currentLib = libKom['name']
        if(currentLib not in libraries):
            return False
    return True
    

def getSkipStatuses(series, name, mangas, forceUpdateFull, currentSerie):
    skipUpdate = False
    skipSync = False
    isFinished = False
    if (series['metadata']['statusLock'] == True and series['metadata']['status'] == 'ENDED'):
        isFinished = True
    if currentSerie is not None :
        if "metadatas" not in currentSerie :
            printC("No metadatas in datas; we force update for " + name, "error")
            isFinished = False
    else:
        currentSerie={}
    if(len(mangas) > 0):
        if(series['name'] not in mangas):
            skipUpdate = True
            skipSync = True

    if (isFinished == True and forceUpdateFull is False):
        printC("Ignoring "+str(name)+" : series terminated and already synchronized", 'warn')
        skipUpdate = True

    return skipUpdate, skipSync