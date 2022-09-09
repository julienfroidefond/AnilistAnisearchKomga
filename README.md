# AnilIst / Anisearch metadata scraper for Komga

2 functions : 
- Get matadata from anilist; complete with anisearch
- Synchronize anilist personal lists

## About this fork

I have updated and done some private work :

- Get Total number of books (always japanese)
- Adding LIBS env; format like MANGAS for only some libs
- Force status with japanese status
- removing some bad caracters on summary
- instead of getting the basic name for search;, getting the metadata title
- setting always language to fr
- print push data only if fails
- not resynchronizing if status is ended and status lock (we consider that if status lock; it has been by the synchronizer). If you want to resync; you just have to remove lock state on status in the UI.
- info in print has been reviewed : colors and typings :)
- review code about json to string
- Anilist synchronizer !
- refacto and split by files
- you can put an extra parameter : onlyResume for cron job purpose (`python mangaMetadata.py OnlyResume`) It will just print warn/success/errors

## About Anilist sync

Go to https://anilist.co/settings/developer and click "Create New Api v2 client", then enter your client name and redirect URI : https://anilist.co/api/v2/oauth/pin. After clicking Save you'll receive your client ID and secret.
You have to define in environment this variables :

- `ACTIVATEANILIST="true"`
- `ANILISTID="1234"`
- `ANILISTSECRET="abcdefgh"`
- `ANILISTUSERNAME="myusername"`

The script will ask you the code for generating token (just follow the cli).
The token is registered in the datas.json file. Just delete it in the file to reset.

New file for sync has appears : `datas.json`. You can change ids of anilist if the matching was not good.
FYI : On anilist, we filter on manga and no hentai.

# Original readme

## Introduction

This Script gets a list of every manga available on your Komga instance,
looks it up one after another on [Anisearch](https://www.anisearch.com/) and gets the metadata for the specific series.
This metadata then gets converted to be compatible to Komga and then gets sent to the server instance and added to the manga entry.

See below for a list of supported attributes and languages

## Requirements

- A Komga instance with access to the admin account
- Either Windows/Linux/MAc or alternatively Docker
- Python installed if using Windows, Linux or Mac natively

## Supported Languages

These languages have to be set in the config under `anisearchlang`.

If the chosen language has no summary available, the english summary will be used.
For status and publisher the japanese metadata will be used as a fallback.

I tried to test the languages as best as I could, but if I missed something please make an Issue and tell me whats wrong :)

- German
- English
- Spanish
- French
- Italian
- Japanese

## Parsed Attributes

From Anilist :

- [x] Status
- [x] Summary
- [ ] Publisher
- [ ] Age rating (not supported for now, does Anisearch even have this?)
- [x] Genres
- [x] Tags

From Anisearch :

- [x] Books total count


## Getting started (Native)

1. Install the requirements using `pip install -r requirements.txt`
2. Init Playwright using `playwright install`
3. Rename `config.template.py` to `config.py` and edit the url, email and password to match the ones of your komga instance (User needs to have permission to edit the metadata).
   The "mangas" array can be filled with the names of mangas which are supposed to be updated, if it is left empty every manga will be updated.
4. Run the script using `python mangaMetadata.py`

## Getting started (Docker)

1. Run the docker image (replace the url, email and password with the one of your Komga instance (user needs to have permission to edit the metadata)) using

```
docker run \
  -e KOMGAURL=https://komga.com \
  -e KOMGAEMAIL=adminemail@komga.com \
  -e KOMGAPASSWORD=12345 \
  -e LANGUAGE=German \
  --name anisearchkomga \
  pfuenzle/anisearchkomga:latest
```

Hint: Replace \ with ` when using Powershell

Alternatively, you could run the docker-compose to get a running container

### Additional Environment Variables

- `MANGAS="Manga1,Manga2"` - This can be used to give a comma seperated list of mangas which are supposed to be updated. If it is left blank, every manga will be updated.
- `LIBS="Lib1,Lib2"` - This can be used to filter a library Komga
