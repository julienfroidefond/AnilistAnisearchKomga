import requests, json, webbrowser, math, re

from utils import printC, logStatus, getSerieByName

def anilistGet(currentSerie, forceUpdateFull):

    name = currentSerie["name"]
    printC("get datas JSON anilist for "+name)
    try:
        if("anilistInfo" not in currentSerie.keys() or forceUpdateFull):
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
                        status
                        tags {
                            name
                        }
                        description
                        genres
                        endDate {
                            year
                            month
                            day
                        }
                        startDate {
                            year
                            month
                            day
                        }
                    }
                }
            }
            '''
            variables = {
                'search': name
            }
            url = 'https://graphql.anilist.co'
            printC("Getting info from anilist")
            response = requests.post(url, json={'query': query, 'variables': variables})
            resData = json.loads(response.text)
            if "data" in resData.keys():
                if(len(resData["data"]["Page"]["media"]) > 0):
                    printC("Successfully get from anilist for " + name, 'success')
                    logStatus(currentSerie, "anilist get", "Manga found all ok", True)
                    return resData["data"]["Page"]["media"][0]
                else:
                    # printC(json.dumps(resData,skipkeys = True),'debug')
                    # printC(json.dumps(query,skipkeys = True),'debug')
                    # printC(json.dumps(variables,skipkeys = True),'debug')
                    printC("Manga not found on anilist : "+name, "error")
                    logStatus(currentSerie, "anilist get", "Manga not found on anilist", True)
                    return {}
            else:
                printC(resData,"debug")
                return {}
        else:
            printC("Manga already in local")
            logStatus(currentSerie, "anilist get", "Manga already in local", True)
            return currentSerie["anilistInfo"]

    except Exception as e:
        printC(str(e), "debug")
        printC("Failed to get from anilist", 'error')
        return {}

def aniListConnect(anilistAccessToken, anilistClientId, anilistSecret):
    accessToken=''
    if(anilistAccessToken == ""):
        input("Now we will invite you to generate a code for doing update in your Anilit account (Press Enter)")
        webbrowser.open("https://anilist.co/api/v2/oauth/authorize?client_id="+anilistClientId+"&redirect_uri=https://anilist.co/api/v2/oauth/pin&response_type=code")
        code = input("Paste here : \n")
        response =requests.post("https://anilist.co/api/v2/oauth/token", headers = {
            "Content-Type": "application/json",
            'Accept': 'application/json'
            }, json={
            'grant_type': 'authorization_code',
            'client_id': anilistClientId,
            'client_secret': anilistSecret,
            'redirect_uri': 'https://anilist.co/api/v2/oauth/pin',
            'code': code
        })
        print(json.loads(response.text))
        accessToken = json.loads(response.text)['access_token']
        printC("Successfully get a token from anilist for user", "success")
    else:
        accessToken = anilistAccessToken
    return accessToken

def getUserCurrentLists(username):
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
 
def anilistAdd(anilistId, name, series, userMediaList, accessToken, currentSerie):
    md = currentSerie["metadatas"]
    booksReadCount = series['booksReadCount']
    totalBookCount = series['metadata']['totalBookCount']
    totalChaptersCount = md["totalChaptersCount"]

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
                if currentUserMedia is not None:
                    progressChapters= math.ceil(currentUserMedia['progressVolumes'] / chapByVol)

        hasToUpdate = True
        if(currentUserMedia):
            if(currentUserMedia['status'] != "PLANNING" and currentUserMedia['status'] != "COMPLETED" and currentUserMedia['status'] != "CURRENT") :
                printC("Not updating anilist : preserving status : " + currentUserMedia['status'])
                logStatus(currentSerie, "anilist push", "Not updating anilist : preserving status : " + currentUserMedia['status'], True)
                hasToUpdate = False
            if(currentUserMedia['status'] == status and booksReadCount <= currentUserMedia['progressVolumes']):
                printC("Not updating anilist : preserving volumes count : " + str(currentUserMedia['progressVolumes']) + " VS LOCAL : " +str(booksReadCount))
                logStatus(currentSerie, "anilist push", "Not updating anilist : preserving volumes count : " + str(currentUserMedia['progressVolumes']) + " VS LOCAL : " +str(booksReadCount), True)
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
                logStatus(currentSerie, "anilist push success", "synchronized  in status " + status + " with " + str(booksReadCount) + " volumes and " + str(progressChapters) + " chapters", False)
            else:
                printC("Error when uploading on anilist : "+jsonRes, "error")
                logStatus(currentSerie, "anilist push", "Error " + jsonRes, True)

CLEANR = re.compile('<.*?>') 
def cleanhtml(raw_html):
    cleantext = re.sub(CLEANR, '', raw_html)
    return cleantext

def mapAnilistToKomga(anilistData):
    tags=[]
    if("tags"in anilistData.keys()):
        for tag in anilistData["tags"]:
            tags.append(tag['name'])
        
        status = anilistData["status"]
        casestatus="ONGOING"
        if(status != ""):
            if(status == "RELEASING"):
                casestatus = "ONGOING"
            elif(status == "NOT_YET_RELEASED"):
                casestatus = "ONGOING"
            elif(status == "CANCELLED"):
                casestatus = "ABANDONED"
            elif(status == "FINISHED"):
                casestatus = "ENDED"
       
        cleanDesc = cleanhtml(anilistData["description"])
        
        return {
            "language": "fr",
            "languageLock": True,
            "status": casestatus,
            "statusLock": True,
            "summary": cleanDesc,
            "summaryLock": True,
            "genres": anilistData["genres"],
            "genresLock": True,
            "tags": tags,
            "tagsLock": True,
            "totalBookCount": anilistData["volumes"],
            "totalBookCountLock": True
        }
    else:
        return {}