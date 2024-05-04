# -*- coding: utf-8 -*-
# TV Ontario Kodi Video Addon
#
from t1mlib import t1mAddon
import json
import xbmc
import xbmcplugin
import xbmcgui
import sys
import requests
from time import strftime, strptime
 
URL_GRAPHQL_SERVER = "https://hmy0rc1bo2.execute-api.ca-central-1.amazonaws.com/graphql"
USERAGENT = 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.101 Safari/537.36'
HEADERS = {'User-Agent': USERAGENT,
           'origin': 'https://www.tvo.org',
           'referer': 'https://www.tvo.org/',
           'Accept': "application/json, text/javascript, text/html,*/*",
           'Accept-Encoding': 'gzip,deflate,sdch',
           'Accept-Language': 'en-US,en;q=0.8'}
AGENDAPAGESIZE = 20
SEARCHPAGESIZE = 100
PODCASTPAGESIZE = 50

class myAddon(t1mAddon):

  def getAddonMenu(self, url, ilist):
      json_data = {
        'operationName': 'SeriesAndDocsNav',
        'variables': {},
        'query': 'query SeriesAndDocsNav {\n getTVOOrgCategoriesMenu {\n categoryTitle\n path\n }\n}\n'
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
          # Screen out 'All' and 'National Geographic'; separate function for 'Series', 'Docs', 'A-Z'
          if name in ['Series', 'Docs', 'A-Z']:
              ilist = self.addMenuItem(name, 'GS', ilist, url+'||3', self.addonIcon, self.addonFanart, infoList, isFolder=True)
          elif name not in ['All', 'National Geographic']:
              ilist = self.addMenuItem(name, 'GS', ilist, url+'||1', self.addonIcon, self.addonFanart, infoList, isFolder=True)
      ilist = self.addMenuItem('Podcasts', 'GS', ilist, '||2', self.addonIcon, self.addonFanart, {}, isFolder=True)
      ilist = self.addMenuItem('Schedule', 'GL', ilist, '||0', self.addonIcon, self.addonFanart, {}, isFolder=True)
      ilist = self.addMenuItem('Search', 'SE', ilist, '||1||0', self.addonIcon, self.addonFanart, {}, isFolder=True)
      return ilist

 
  def getAddonShows1(self, url, ilist):  # Get shows other than podcasts, 'Series', 'Docs' and 'A-Z'
      json_data = {
        'operationName': 'SeriesDocsCategory',
        'variables': {
          # Able to get ALL shows by setting 'first' and 'after' to 0
          'first': 0,
          'after': 0,
          'category': url,
        },
        'query': 'query SeriesDocsCategory($category: String!, $first: Int, $after: Int) {\n categoryData: getTVOOrgCategoriesByName(\n name: $category\n first: $first\n after: $after\n) {\n totalItems\n content {\n programTitle\n path\n imageSrc\n episode\n program {\n coverImage\n }\n }\n }\n}\n'
      }
      response = requests.post(URL_GRAPHQL_SERVER, headers=HEADERS, json=json_data)
      shows_js = json.loads(response.text)
 
      # Loop through all shows in the category
      for show in shows_js["data"]["categoryData"][0]["content"]:
          episodes = show["episode"]
          if str(episodes).isdigit(): episodes = int(episodes)
          if episodes > 1:
              name = "%s (Series)" % (show["programTitle"])
          else:
              name = show["programTitle"]
          url    = show["path"]
          thumb  = show["imageSrc"]
          plot   = show["programTitle"]
          cover  = show["program"]["coverImage"]
          if cover == "": cover = thumb
          infoList= {'mediatype': 'tvshow',
                     'Title': name,
                     'episode': episodes,
                     'season': 1,
                     'Plot': plot}
          if 'The Agenda' in name:
              ilist = self.addMenuItem(name, 'GE', ilist, url+'||2||0', cover, thumb, infoList, isFolder=True)
          elif episodes > 1:
              ilist = self.addMenuItem(name, 'GE', ilist, url+'||1||0', cover, thumb, infoList, isFolder=True)
          else:
              ilist = self.addMenuItem(name, 'GM', ilist, url, cover, thumb, infoList, isFolder=True)
      return ilist
 
 
  def getAddonShows2(self, url, ilist):   # Get TVO Podcasts
      json_data = {
        'operationName': 'AllPodcastPrograms',
        'variables': {},
        'query': 'query AllPodcastPrograms {\n programs: getTVOOrgAllPodcastPrograms {\n program {\n omnySlug\n title\n category\n featuredImage\n description\n defaultPlaylist {\n totalItems\n }\n }\n }\n}\n'
      }
      response = requests.post(URL_GRAPHQL_SERVER, headers=HEADERS, json=json_data)
      shows_js = json.loads(response.text)
 
      # Loop through all shows in the category
      for j in shows_js["data"]["programs"]:
          show     = j["program"]
          episodes = show["defaultPlaylist"]["totalItems"]
          name     = "%s (%s episodes)" % (show["title"], episodes)
          url      = show["omnySlug"]
          thumb    = show["featuredImage"]
          plot     = show["description"]
          if str(episodes).isdigit(): episodes = int(episodes)
          infoList= {'mediatype': 'tvshow',
                     'Title': name,
                     'episode': episodes,
                     'season': 1,
                     'Plot': plot}
          ilist = self.addMenuItem(name, 'GE', ilist, url+'||3||1', thumb, thumb, infoList, isFolder=True)
      return ilist


  def getAddonShows3(self, url, ilist):   # Get 'Docs', 'Series' and 'A-Z'
      json_data = {
        'operationName':'SeriesDocsFilterContent',
        'variables':{
          'filter': url,
          # Able to get ALL shows by setting 'first' to 0
          'first':0
        },
        'query':'query SeriesDocsFilterContent($filter: String, $first: Int) {\n filterData: getTVOOrgCategoriesByFilter(\n filter: $filter\n first: $first\n ) {\n content {\n programTitle\n path\n imageSrc\n season\n episode\n program {\n coverImage\n featuredImage\n }\n }\n }\n}\n'
      }
      response = requests.post(URL_GRAPHQL_SERVER, headers=HEADERS, json=json_data)
      shows_js = json.loads(response.text)
 
      # Loop through all shows in the category
      for show in shows_js["data"]["filterData"][0]["content"]:
          seasons  = show["season"]
          episodes = show["episode"]
          url      = show["path"]
          plot     = show["programTitle"]
          thumb    = show["imageSrc"]
          cover    = show["program"]["coverImage"]
          if str(seasons).isdigit(): seasons = int(seasons)
          if str(episodes).isdigit(): episodes = int(episodes)
          if cover == "": cover = thumb
          if episodes > 1:
              name = "%s (Series)" % (show["programTitle"])
          else:
              name = show["programTitle"]
          infoList= {'mediatype': 'tvshow',
                     'Title': name,
                     'episode': episodes,
                     'season': seasons,
                     'Plot': plot}
          if 'The Agenda' in name:
              ilist = self.addMenuItem(name, 'GE', ilist, url+'||2||0', cover, thumb, infoList, isFolder=True)
          elif episodes > 1:
              ilist = self.addMenuItem(name, 'GE', ilist, url+'||1||0', cover, thumb, infoList, isFolder=True)
          else:
              ilist = self.addMenuItem(name, 'GM', ilist, url, cover, thumb, infoList, isFolder=True)
      return ilist
 

  def getAddonShows(self, url, ilist):
      # Split into option and show url
      showurl = url.split('||', 1)[0]
      option  = url.split('||', 1)[1] # 1:Most shows other than -> | 2:Podcasts | 3: 'Docs', 'Series', 'A-Z'
      if   option == '1':
          ilist = self.getAddonShows1(showurl, ilist)
      elif option == '2':
          ilist = self.getAddonShows2(showurl, ilist)
      elif option == '3':
          ilist = self.getAddonShows3(showurl, ilist)
      return ilist


  def getAddonEpisodes1(self, url, ilist):
      self.defaultVidStream['width']  = 1280
      self.defaultVidStream['height'] = 720
      json_data = {
        'operationName': 'ProgramOverview',
        'variables': {
          'slug': url,
        },
        'query': 'query ProgramOverview($slug: String) {\n getTVOOrgProgramOverview(slug: $slug) {\n title\n description\n featuredImage\n seasons {\n season\n episodes {\n episodeTitle\n imageSrc\n path\n duration\n episode\n description\n airDate\n}\n }\n }\n}\n'
      }
      response = requests.post(URL_GRAPHQL_SERVER, headers=HEADERS, json=json_data)
      episodes_js = json.loads(response.text)
 
      show_title= episodes_js["data"]["getTVOOrgProgramOverview"]["title"]
      # Loop through seasons
      for j in episodes_js["data"]["getTVOOrgProgramOverview"]["seasons"]:
          season = j["season"]
          if str(season).isdigit(): season = int(season)
          for k in j["episodes"]:
              episode = k["episode"]
              title   = k["episodeTitle"]
              name    = 'S%sE%s - %s' % (str(season), str(episode), str(title))
              url     = k["path"]
              thumb   = k["imageSrc"]
              plot    = k["description"]
              aired   = k["airDate"]
              try:
                  dateraw  = strptime(aired, '%b %d, %Y')
                  datedash = strftime('%Y-%m-%d', dateraw)
                  datedot  = strftime("%d.%m.%Y", dateraw)
              except ValueError:
                  datedash = '1970-01-01'
                  datedot  = '01.01.1970'
              if str(episode).isdigit(): episode = int(episode)
              duration= sum(x * int(t) for x,t in zip([1, 60, 3600], reversed(k["duration"].split(":"))))
              infoList= {'mediatype': 'episode',
                         'TVShowTitle': show_title,
                         'Title': name,
                         'duration': duration,
                         'episode': episode,
                         'season': season,
                         'premiered': datedash,
                         'date': datedot,
                         'Plot': plot}
              ilist = self.addMenuItem(name, 'GV', ilist, url, thumb, thumb, infoList, isFolder=False)
      return ilist

 
  def getAddonEpisodes2(self, url, ilist):    # For 'The Agenda' as it uses a unique post request
      self.defaultVidStream['width']  = 1280
      self.defaultVidStream['height'] = 720
      # Split into relative list position and show url
      showurl  = url.split('||', 1)[0]
      position = url.split('||', 1)[1]
      json_data = {
        'operationName': 'AgendaRecentSegments',
        'variables': {
          'name'  : 'theagenda',
          'first' : int(AGENDAPAGESIZE),
          'after' : int(position),
        },
        'query': 'query AgendaRecentSegments($name: String!, $first: Int, $after: Int) {\n recentSegments: getTVOSpecialProgramContent(\n name: $name\n first: $first\n after: $after\n ) {\n totalItems\n content {\n path\n imageSrc\n season\n episode\n episodeTitle\n description\n airDate\n duration\n }\n }\n}\n'
      }
      response = requests.post(URL_GRAPHQL_SERVER, headers=HEADERS, json=json_data)
      agenda_js = json.loads(response.text)
 
      numShows = agenda_js["data"]["recentSegments"]["totalItems"]
      show_title= 'The Agenda'
      # Loop through segments
      for j in agenda_js["data"]["recentSegments"]["content"]:
          season  = j["season"]
          episode = j["episode"]
          name    = j["episodeTitle"]
          url     = j["path"]
          thumb   = j["imageSrc"]
          aired   = j["airDate"]
          plot    = j["description"]
          try:
              dateraw  = strptime(aired, '%b %d, %Y')
              datedash = strftime('%Y-%m-%d', dateraw)
              datedot  = strftime("%d.%m.%Y", dateraw)
          except ValueError:
              datedash = '1970-01-01'
              datedot  = '01.01.1970'
          if str(season).isdigit(): season = int(season)
          if str(episode).isdigit(): episode = int(episode)
          duration= sum(x * int(t) for x,t in zip([1, 60, 3600], reversed(j["duration"].split(":"))))
          infoList= {'mediatype': 'episode',
                     'TVShowTitle': '%s - Season:%s, Episode:%s' % (show_title,str(season),str(episode)),
                     'Title': name,
                     'duration': duration,
                     'episode': episode,
                     'season': season,
                     'Plot': plot,
                     'premiered': datedash,
                     'date': datedot,
          }
          ilist = self.addMenuItem(name, 'GV', ilist, url, thumb, thumb, infoList, isFolder=False)
      # Add "MORE" prompt if there are more shows to list
      if (int(position) + int(AGENDAPAGESIZE)) < numShows:
          nextUrl = showurl + '||2||' + str(int(position)+int(AGENDAPAGESIZE))
          ilist = self.addMenuItem('[COLOR red]MORE[/COLOR]', 'GE', ilist, nextUrl, self.addonIcon, self.addonFanart, {}, isFolder=True)
      return ilist
 

  def getAddonEpisodes3(self, url, ilist):  # Get TVO Podcast episodes
      # Split into podcast url and relative list position 
      podurl = url.split('||', 1)[0]
      page   = int(url.split('||', 1)[1])
      json_data = {
        'operationName': 'Podcast',
        'variables': {
          'slug'      : podurl,
          'first'     : PODCASTPAGESIZE,
          'pageNumber': page
        },
        'query': 'query Podcast($omnyID: String, $slug: String, $first: Int, $pageNumber: Int) {\n podcast: getTVOOrgPodcastProgram(\n omnyID: $omnyID\n slug: $slug\n first: $first\n pageNumber: $pageNumber\n ) {\n program {\n title\n featuredImage\n defaultPlaylist {\n totalItems\n content {\n omnyAssetUrl\n featuredImage\n title\n description\n season\n episode\n publishedAt\n duration\n }\n }\n }\n }\n}\n'
      }
      response = requests.post(URL_GRAPHQL_SERVER, headers=HEADERS, json=json_data)
      episodes_js = json.loads(response.text)
 
      show_title= episodes_js["data"]["podcast"]["program"]["title"]
      numEpisodes= episodes_js["data"]["podcast"]["program"]["defaultPlaylist"]["totalItems"]
      # Loop through episodes
      for j in episodes_js["data"]["podcast"]["program"]["defaultPlaylist"]["content"]:
          season  = j["season"]
          episode = j["episode"]
          name    = j["title"]
          url     = j["omnyAssetUrl"]
          thumb   = j["featuredImage"]
          plot    = j["description"]
          duration= j["duration"]
          aired   = j["publishedAt"]
          try:
              dateraw  = strptime(aired[:10], '%Y-%m-%d')
              datedash = strftime('%Y-%m-%d', dateraw)
              datedot  = strftime("%d.%m.%Y", dateraw)
          except ValueError:
              datedash = '1970-01-01'
              datedot  = '01.01.1970'
          if str(season).isdigit(): season = int(season)
          if str(episode).isdigit(): episode = int(episode)
          if str(duration).isdigit(): duration = int(duration)
          infoList= {'mediatype': 'episode',
                     'TVShowTitle': show_title,
                     'Title': name,
                     'duration': duration,
                     'episode': episode,
                     'season': season,
                     'premiered': datedash,
                     'date': datedot,
                     'Plot': plot}
          ilist = self.addMenuItem(name, 'GA', ilist, url, thumb, thumb, infoList, isFolder=False)
      # Add "MORE" prompt if there are more episodes to list
      if (int(page) * int(PODCASTPAGESIZE)) < numEpisodes:
          nextUrl = podurl + '||3||' + str(int(page)+1)
          ilist = self.addMenuItem('[COLOR red]MORE[/COLOR]', 'GE', ilist, nextUrl, self.addonIcon, self.addonFanart, {}, isFolder=True)
      return ilist

 
  def getAddonEpisodes(self, url, ilist):
      show  = url.split('||', 2)[0]
      option= url.split('||', 2)[1]  # 1:All shows except -> | 2:The Agenda | 3:Podcasts
      page  = url.split('||', 2)[2]
      if   option == '1':
          ilist = self.getAddonEpisodes1(show, ilist)
      elif option == '2':
          ilist = self.getAddonEpisodes2(show+'||'+page, ilist)
      elif option == '3':
          ilist = self.getAddonEpisodes3(show+'||'+page, ilist)
      return ilist


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

      if 'errors' in movie_js:
          ilist = self.getAddonEpisodes1(url, ilist)
      else: 
          movie = movie_js["data"]["getTVOOrgVideo"]
          name    = movie["title"]
          url     = movie["nodeUrl"]
          thumb   = movie["thumbnail"]
          cover   = movie["program"]["coverImage"]
          plot    = movie["description"]
          duration= sum(x * int(t) for x,t in zip([1, 60, 3600], reversed(movie["length"].split(":"))))
          infoList= {'mediatype': 'movie',
                     'Title': name,
                     'duration': duration,
                     'Plot': plot}
          ilist = self.addMenuItem(name, 'GV', ilist, url, cover, thumb, infoList, isFolder=False)
      return ilist
 

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


  def getAddonAudio(self, url):
      liz = xbmcgui.ListItem(path=url)
      xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)


  def getAddonSearchQuery(self, url, ilist):  # First step in two-step process; to fix the refresh asking for input again
      query = xbmcgui.Dialog().input('Enter search term')
      infoList = {'Title': "Search for: '%s'" % query}
      ilist = self.addMenuItem('Results', 'SE', ilist, query+'||2||1', self.addonIcon, self.addonFanart, infoList, isFolder=True)
      return ilist


  def getAddonSearchSearch(self, url, ilist):
      query = url.split('||', 1)[0]
      page  = int(url.split('||', 1)[1])
      self.defaultVidStream['width']  = 1280
      self.defaultVidStream['height'] = 720

      URL_SWIFTYPE_SERVER = "https://search-api.swiftype.com/api/v1/public/engines/search.json?"
      json_data = { 'q':query, 'page':str(page), 'per_page':str(SEARCHPAGESIZE), 'engine_key':'aBsuBkeq84LGLQsYdWMV'}
      response = requests.post(URL_SWIFTYPE_SERVER, headers=HEADERS, json=json_data)
      search_js = json.loads(response.text)
      # Loop through the search results
      for j in search_js["records"]["page"]:
          if j["type"] == 'video':
              title  = j["title"]
              name   = j["title"]
              thumb  = j["image"]
              aired  = j["published_at"]
              try:
                  dateraw  = strptime(aired[:10], '%Y-%m-%d')
                  datedash = strftime('%Y-%m-%d', dateraw)
                  datedot  = strftime("%d.%m.%Y", dateraw)
              except ValueError:
                  datedash = '1970-01-01'
                  datedot  = '01.01.1970'
              url    = j["url"].replace('https://www.tvo.org','')
              plot   = j["desc"]
              infoList = {'mediatype': 'movie',
                          'TVShowTitle': title,
                          'Title': title,
                          'Plot': plot,
                          'duration': 0,
                          'episode': 0,
                          'premiered': datedash,
                          'date': datedot,
              }
              ilist = self.addMenuItem(name, 'GV', ilist, url, thumb, thumb, infoList, isFolder=False)
      # Add "MORE" prompt if there are more search results to list
      pages = search_js["info"]["page"]["num_pages"]
      if page < int(pages):
          nextUrl = query + '||2||' + str(page+1)
          ilist = self.addMenuItem('[COLOR red]MORE[/COLOR]', 'SE', ilist, nextUrl, self.addonIcon, self.addonFanart, {}, isFolder=True)
      return ilist


  def getAddonSearch(self, url, ilist):
      query = url.split('||', 2)[0]
      option= url.split('||', 2)[1]  # 1:Query | 2:Search
      page  = url.split('||', 2)[2]
      if   option == '1':
          ilist = self.getAddonSearchQuery(query,ilist)
      elif option == '2':
          ilist = self.getAddonSearchSearch(query+'||'+page,ilist)
      return ilist


  def getAddonListing(self, url, ilist):   # Get TVO Schedule
      day    = url.split('||', 1)[0]
      option = int(url.split('||', 1)[1])
      if option == 0:   # Display the list of available days
          json_data = {
            'operationName': 'ScheduleDateFilter',
            'variables': {},
            'query': 'query ScheduleDateFilter {\n getTVOOrgScheduleDateFilters {\n day\n monthDate\n fullDate\n }\n}\n'
          }
          response = requests.post(URL_GRAPHQL_SERVER, headers=HEADERS, json=json_data)
          days_js = json.loads(response.text)
          # Gather the days
          for j in days_js["data"]["getTVOOrgScheduleDateFilters"]:
              name     = '%s, %s' % (j["day"], j["monthDate"])
              url      = j["fullDate"]
              infoList = {'mediatype': 'movie',
                          'Title': name,
              }
              ilist = self.addMenuItem(name, 'GL', ilist, url+'||1', self.addonIcon, self.addonFanart, infoList, isFolder=True)
      elif option == 1 or option == 2:  # Option 1: display just evening and late night shows; Option 2: display the whole day
          if option == 1:
              ilist = self.addMenuItem('[COLOR yellow]See full day schedule[/COLOR]', 'GL', ilist, day+'||2', self.addonIcon, self.addonFanart, {}, isFolder=True)
          json_data = {
            'operationName': 'ScheduleDayEpisodes',
            'variables': {'date': day },
            'query': 'query ScheduleDayEpisodes($date: String) {\n getTVOOrgScheduleFullDay(date: $date) {\n timeOfDay\n airDate\n title\n seriesTitle\n description\n \n}\n}\n'
          }
          response = requests.post(URL_GRAPHQL_SERVER, headers=HEADERS, json=json_data)
          days_js = json.loads(response.text)
          # Gather the programming
          for j in days_js["data"]["getTVOOrgScheduleFullDay"]:
              seriesTitle = j["seriesTitle"]
              description = j["description"]
              title       = j["title"]
              airDate     = j["airDate"]
              timeOfDay   = j["timeOfDay"]
              url         = j["title"]
              infoList = {'mediatype': 'episode',
                          'Title': '%s - %s (%s)' % (airDate, seriesTitle, title),
                          'Plot' : '%s\n"%s"\n%s' % (day, title, description),
              }
              if   option == 1 and timeOfDay in ['Evening', 'Late Night']:
                  ilist = self.addMenuItem('', 'GL', ilist, url+'||3', self.addonIcon, self.addonFanart, infoList, isFolder=True)
              elif option == 2:
                  ilist = self.addMenuItem('', 'GL', ilist, url+'||3', self.addonIcon, self.addonFanart, infoList, isFolder=True)
      return ilist

