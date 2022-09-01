import requests, json, webbrowser, math

from utils import printC, logStatus

def anilistGet(name, seriesID, datas):
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

def aniListConnect(datas):
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

def getUserCurrentLists(username, datas):
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
        'userName': username
    }
    url = 'https://graphql.anilist.co'
    printC("Getting user's lists from anilist for " + username)
    response = requests.post(url, json={'query': query, 'variables': variables})
    resData = json.loads(response.text)
    return resData['data']['Page']['mediaList']
 
def anilistAdd(anilistData, name, series, userMediaList, accessToken, md, datas):
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