# -*- coding: utf-8 -*-
# TV Ontario Kodi Video Addon
#
from t1mlib import t1mAddon
import json
import re
import os
import xbmc
import xbmcplugin
import xbmcgui
import sys
import requests
from datetime import datetime
 
URL_GRAPHQL_SERVER = "https://hmy0rc1bo2.execute-api.ca-central-1.amazonaws.com/graphql"
USERAGENT = 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.101 Safari/537.36'
HEADERS = {'User-Agent': USERAGENT,
           'origin': 'https://www.tvo.org',
           'referer': 'https://www.tvo.org/',
           'Accept': "application/json, text/javascript, text/html,*/*",
           'Accept-Encoding': 'gzip,deflate,sdch',
           'Accept-Language': 'en-US,en;q=0.8'}
PAGESIZE = 20
SEARCHPAGESIZE = '100'

class myAddon(t1mAddon):
 
  def getAddonMenu(self, url, ilist):
      json_data = {
        'operationName': 'SeriesAndDocsNav',
        'variables': {},
        'query': 'query SeriesAndDocsNav {\n  getTVOOrgCategoriesMenu {\n categoryTitle\n path\n }\n}\n'
      }
      response = requests.post(URL_GRAPHQL_SERVER, headers=HEADERS, json=json_data)
      cats_js = json.loads(response.text)
      for cat in cats_js["data"]["getTVOOrgCategoriesMenu"]:
          name = cat["categoryTitle"]
          plot = cat["path"]
          url  = name
          infoList = {'mediatype':'tvshow',
                      'Title': name,
                      'Plot': plot}
          # Include entries that are 'SeriesDocsCategory' rather than 'SeriesDocsFilterContentnot'
          if (name not in ['All', 'Series', 'Docs', 'A-Z', 'National Geographic']):
              ilist = self.addMenuItem(name, 'GS', ilist, url, self.addonIcon, self.addonFanart, infoList, isFolder=True)
      ilist = self.addMenuItem('Search', 'SE', ilist, '|0', self.addonIcon, self.addonFanart, {'Title': 'Search'}, isFolder=True)
      return(ilist)
 
  def getAddonShows(self, url, ilist):
      json_data = {
        'operationName': 'SeriesDocsCategory',
        'variables': {
          # Able to get all shows in a category by setting 'first' and 'after' to 0
          'first': 0,
          'after': 0,
          'category': url,
        },
        'query': 'query SeriesDocsCategory($category: String!, $first: Int, $after: Int) {\n categoryData: getTVOOrgCategoriesByName(\n name: $category\n first: $first\n after: $after\n) {\n totalItems\n content {\n programTitle\n path\n imageSrc\n episode\n program {\n coverImage\n }\n }\n }\n}\n'
      }
      response = requests.post(URL_GRAPHQL_SERVER, headers=HEADERS, json=json_data)
      shows_js = json.loads(response.text)
 
      # Get total number of shows in the category
      numShows = shows_js["data"]["categoryData"][0]["totalItems"]
 
      # Loop through all shows in the category
      for show in shows_js["data"]["categoryData"][0]["content"]:
          episodes = show["episode"]
          if (int(episodes) > 1):
              name = "%s (Series)" % (show["programTitle"])
          else:
              name = show["programTitle"]
          url   = show["path"]
          thumb = show["imageSrc"]
          plot  = show["programTitle"]
          cover = show["program"]["coverImage"]
          if cover == "": cover = thumb
          infoList= {'mediatype': 'tvshow',
                     'Title': name,
                     'Plot': plot}
          if 'The Agenda' in name:
              ilist = self.addMenuItem(name, 'GL', ilist, url+'|0', cover, thumb, infoList, isFolder=True)
          elif (int(episodes) > 1):
              ilist = self.addMenuItem(name, 'GE', ilist, url, cover, thumb, infoList, isFolder=True)
          else:
              ilist = self.addMenuItem(name, 'GM', ilist, url, cover, thumb, infoList, isFolder=True)
      return(ilist)
 

### Using 'getAddonListing' for 'The Agenda' since it uses a different query than the 
### other shows and 'getAddonListing' is already in t1mlib.py with an 'episodes' format.

  def getAddonListing(self, url, ilist):
      self.defaultVidStream['width']  = 1280
      self.defaultVidStream['height'] = 720
      # Split into relative list position and category url
      caturl   = url.split('|', 1)[0]
      position = url.split('|', 1)[1]
      json_data = {
        'operationName': 'AgendaRecentSegments',
        'variables': {
          'name'  : 'theagenda',
          'first' : int(PAGESIZE),
          'after' : int(position),
        },
        'query': 'query AgendaRecentSegments($name: String!, $first: Int, $after: Int) {\n recentSegments: getTVOSpecialProgramContent(\n name: $name\n first: $first\n after: $after\n ) {\n totalItems\n content {\n path\n imageSrc\n season\n episode\n episodeTitle\n description\n airDate\n duration\n }\n }\n}\n'
      }
      response = requests.post(URL_GRAPHQL_SERVER, headers=HEADERS, json=json_data)
      agenda_js = json.loads(response.text)
 
      numShows = agenda_js["data"]["recentSegments"]["totalItems"]
      show_title= 'The Agenda'
      # Loop through seasons
      for j in agenda_js["data"]["recentSegments"]["content"]:
          season  = j["season"]
          episode = j["episode"]
          name    = j["episodeTitle"]
          url     = j["path"]
          thumb   = j["imageSrc"]
          aired   = j["airDate"]
          plot    = '%s\nAir Date: %s, Season:%s, Episode:%s' % (j["description"], aired, str(season), str(episode))
          duration= sum(x * int(t) for x,t in zip([1, 60, 3600], reversed(j["duration"].split(":"))))
          infoList= {'mediatype': 'episode',
                     'TVShowTitle': '%s - Season:%s, Episode:%s' % (show_title,str(season),str(episode)),
                     'Title': name,
                     'Duration': duration,
                     'Plot': plot,
                     'premiered': str(datetime.strptime(aired, '%b %d, %Y').date())}
          ilist = self.addMenuItem(name, 'GV', ilist, url, thumb, thumb, infoList, isFolder=False)
      # Add "MORE" prompt if there are more shows to list
      if ((int(position)+int(PAGESIZE)) < numShows):
          nextUrl = caturl + '|' + str(int(int(position)+int(PAGESIZE)))
          ilist = self.addMenuItem('[COLOR red]MORE[/COLOR]', 'GL', ilist, nextUrl, self.addonIcon, self.addonFanart, {}, isFolder=True)
      return(ilist)
 
  def getAddonEpisodes(self, url, ilist):
      self.defaultVidStream['width']  = 1280
      self.defaultVidStream['height'] = 720
      json_data = {
        'operationName': 'ProgramOverview',
        'variables': {
          'slug': url,
        },
        'query': 'query ProgramOverview($slug: String) {\n getTVOOrgProgramOverview(slug: $slug) {\n title\n description\n featuredImage\n seasons {\n season\n episodes {\n episodeTitle\n imageSrc\n path\n duration\n episode\n description\n }\n }\n }\n}\n'
      }
      response = requests.post(URL_GRAPHQL_SERVER, headers=HEADERS, json=json_data)
      episodes_js = json.loads(response.text)
 
      show_title= episodes_js["data"]["getTVOOrgProgramOverview"]["title"]
      # Loop through seasons
      for j in episodes_js["data"]["getTVOOrgProgramOverview"]["seasons"]:
          season   = j["season"]
          for k in j["episodes"]:
              episode = k["episode"]
              name    = 'S%sE%s - %s' % (str(season), str(episode), k["episodeTitle"])
              url     = k["path"]
              thumb   = k["imageSrc"]
              plot    = k["description"]
              duration= sum(x * int(t) for x,t in zip([1, 60, 3600], reversed(k["duration"].split(":"))))
              infoList= {'mediatype': 'episode',
                         'TVShowTitle': show_title,
                         'Title': name,
                         'Duration': duration,
                         'Plot': plot}
              ilist = self.addMenuItem(name, 'GV', ilist, url, thumb, thumb, infoList, isFolder=False)
      return(ilist)
 
  def getAddonMovies(self, url, ilist):
      json_data = {
        'operationName': 'getVideo',
        'variables': {
          'slug': url,
        },
        'query': 'query getVideo($slug: String) {\n getTVOOrgVideo(slug: $slug) {\n nodeUrl\n thumbnail\n title\n program {\n coverImage\n }\n description\n length\n }\n}\n'
      }
      response = requests.post(URL_GRAPHQL_SERVER, headers=HEADERS, json=json_data)
      movie_js = json.loads(response.text)
 
      movie = movie_js["data"]["getTVOOrgVideo"]
      name    = movie["title"]
      url     = movie["nodeUrl"]
      thumb   = movie["thumbnail"]
      cover   = movie["program"]["coverImage"]
      plot    = movie["description"]
      duration= sum(x * int(t) for x,t in zip([1, 60, 3600], reversed(movie["length"].split(":"))))
      infoList= {'mediatype': 'movie',
                 'Title': name,
                 'Duration': duration,
                 'Plot': plot}
      ilist = self.addMenuItem(name, 'GV', ilist, url, cover, thumb, infoList, isFolder=False)
      return(ilist)
 
  def getAddonVideo(self, url):
      json_data = {
        'operationName': 'getVideo',
        'variables': {
          'slug': url,
        },
        'query': 'query getVideo($slug: String) {\n getTVOOrgVideo(slug: $slug) {\n assetUrl\n thumbnail\n description\n length\n }\n}\n'
      }
      response = requests.post(URL_GRAPHQL_SERVER, headers=HEADERS, json=json_data)
      video_js = json.loads(response.text)
 
      # Play video
      vidurl = video_js["data"]["getTVOOrgVideo"]["assetUrl"]
      if vidurl == '':
          return False
      liz = xbmcgui.ListItem(path=vidurl)
      xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)


  def getAddonSearch(self, url, ilist):
      query = url.split('|', 1)[0]
      page  = int(url.split('|', 1)[1])
      if page == 0: query = xbmcgui.Dialog().input('Enter search term')
      page += 1
      self.defaultVidStream['width']  = 1280
      self.defaultVidStream['height'] = 720

      URL_SWIFTYPE_SERVER = "https://search-api.swiftype.com/api/v1/public/engines/search.json?"
      json_data = { 'q':query, 'page':str(page), 'per_page':SEARCHPAGESIZE, 'engine_key':'aBsuBkeq84LGLQsYdWMV'}
      response = requests.post(URL_SWIFTYPE_SERVER, headers=HEADERS, json=json_data)
      search_js = json.loads(response.text)
      # Loop through the search results
      for j in search_js["records"]["page"]:
          if j["type"] == 'video':
              title  = j["title"]
              name   = j["title"]
              thumb  = j["image"]
              aired  = j["published_at"]
              url    = j["url"].replace('https://www.tvo.org','')
              plot   = j["desc"]
              infoList = {'mediatype': 'movie',
                          'TVShowTitle': title,
                          'Title': title,
                          'Plot': plot,
                          'premiered': str(datetime.fromisoformat(aired[:-1]).date()),
              }
              ilist = self.addMenuItem(name, 'GV', ilist, url, thumb, thumb, infoList, isFolder=False)
      # Add "MORE" prompt if there are more search results to list
      pages = search_js["info"]["page"]["num_pages"]
      if page < int(pages):
          nextUrl = query + '|' + str(page)
          ilist = self.addMenuItem('[COLOR red]MORE[/COLOR]', 'SE', ilist, nextUrl, self.addonIcon, self.addonFanart, {}, isFolder=True)
      return(ilist)
