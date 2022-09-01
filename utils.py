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


def printC(msg, type = 'info'):
    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    resume=""
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
    return resume

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