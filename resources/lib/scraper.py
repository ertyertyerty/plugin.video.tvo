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
 
URL_GRAPHQL_SERVER = "https://hmy0rc1bo2.execute-api.ca-central-1.amazonaws.com/graphql"
USERAGENT = 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.101 Safari/537.36'
HEADERS = {'User-Agent': USERAGENT,
           'origin': 'https://www.tvo.org',
           'referer': 'https://www.tvo.org/',
           'Accept': "application/json, text/javascript, text/html,*/*",
           'Accept-Encoding': 'gzip,deflate,sdch',
           'Accept-Language': 'en-US,en;q=0.8'}
PAGESIZE = 20
 
class myAddon(t1mAddon):
 
  def getAddonMenu(self, url, ilist):
      json_data = {
        'operationName': 'SeriesAndDocsNav',
        'variables': {},
        'query': 'query SeriesAndDocsNav {\n  getTVOOrgCategoriesMenu {\n    categoryTitle\n    path\n    __typename\n  }\n}\n',
      }
      response = requests.post(URL_GRAPHQL_SERVER, headers=HEADERS, json=json_data)
      cats_js = json.loads(response.text)
      for cat in cats_js["data"]["getTVOOrgCategoriesMenu"]:
        name = cat["categoryTitle"]
        url = name
        # Append starting "after" position
        url = url
        infoList = {'mediatype':'tvshow',
                    'Title': cat["categoryTitle"],
                    'Plot': cat["path"]}
        # Skip entries that are not 'SeriesDocsCategory', but instead are 'SeriesDocsFilterContent'
        if (name != 'All' and name != 'Series' and name != 'Docs' and name != 'A-Z'):
          ilist = self.addMenuItem(name, 'GS', ilist, url+'|0', self.addonIcon, self.addonFanart, infoList, isFolder=True)
      return(ilist)
 
  def getAddonShows(self, url, ilist):
      # Split into relative list position and category url
      caturl = url.split('|', 1)[0]
      position = url.split('|', 1)[1]
      json_data = {
        'operationName': 'SeriesDocsCategory',
        'variables': {
          'category': caturl,
          'first': int(PAGESIZE),
          'after': int(position),
        },
        'query': 'query SeriesDocsCategory($category: String!, $first: Int, $after: Int) {\n  categoryData: getTVOOrgCategoriesByName(\n    name: $category\n    first: $first\n    after: $after\n  ) {\n    categoryTitle\n    path\n    totalItems\n    content {\n      programTitle\n      path\n      imageSrc\n      imageAlt\n      episode\n      episodeTitle\n      program {\n        coverImage\n        featuredImage\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n',
      }
      response = requests.post(URL_GRAPHQL_SERVER, headers=HEADERS, json=json_data)
      shows_js = json.loads(response.text)
 
      # Get total shows in category
      numShows = shows_js["data"]["categoryData"][0]["totalItems"]
 
      # Loop though shows in category
      for show in shows_js["data"]["categoryData"][0]["content"]:
          episodes = show["episode"]
          if (int(episodes) > 1):
            name = "%s (Series)" % (show["programTitle"])
          else:
            name = show["programTitle"]
          url = show["path"]
          thumb = show["imageSrc"]
          plot = show["path"]
          infoList= {'mediatype': 'tvshow',
                     'Title': name,
                     'Plot': plot}
          if (int(episodes) > 1):
            ilist = self.addMenuItem(name, 'GE', ilist, url, thumb, thumb, infoList, isFolder=True)
          else:
            ilist = self.addMenuItem(name, 'GM', ilist, url, thumb, thumb, infoList, isFolder=True)
      # Add "MORE" prompt if more shows to list
      if ((int(position)+int(PAGESIZE)) < numShows):
          nextUrl = caturl + '|' + str(int(int(position)+int(PAGESIZE)))
          ilist = self.addMenuItem('[COLOR red]MORE[/COLOR]', 'GS', ilist, nextUrl, self.addonIcon, self.addonFanart, {}, isFolder=True)
      return(ilist)
 
 
  def getAddonEpisodes(self, url, ilist):
      self.defaultVidStream['width']  = 640
      self.defaultVidStream['height'] = 480
      json_data = {
        'operationName': 'ProgramOverview',
        'variables': {
          'slug': url,
        },
        'query': 'query ProgramOverview($slug: String) {\n  getTVOOrgProgramOverview(slug: $slug) {\n    title\n    tvoOriginal\n    description\n    summary\n    featuredImage\n    imageAlt\n    ctaText\n    uuid\n    nodeUrl\n    totalEpisodes\n    seasons {\n      season\n      totalEpisodes\n      seasonEpisodes\n      episodes {\n        episodeTitle\n        imageSrc\n        imageAlt\n        path\n        duration\n        episode\n        description\n        airDate\n        videoSource {\n          brightcoveRefId\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n',
      }
      response = requests.post(URL_GRAPHQL_SERVER, headers=HEADERS, json=json_data)
      episodes_js = json.loads(response.text)
 
      show_title= episodes_js["data"]["getTVOOrgProgramOverview"]["title"]
      # Loop though seasons
      sdata_js = episodes_js["data"]["getTVOOrgProgramOverview"]["seasons"]
      for j in sdata_js:
          season   = j["season"]
          edata_js = j["episodes"]
          for k in edata_js:
            episode = k["episode"]
            name    = 's%se%s - %s' % (str(season), str(episode), k["episodeTitle"])
            url     = k["path"]
            thumb   = k["imageSrc"]
            plot    = k["description"]
            timetmp = k["duration"]
            if timetmp.count(':') == 0:
              duration = timetmp
            else:
              if timetmp.count(':') == 1:
                timetmp = "0:" + timetmp
              # Calculate time in seconds
              duration = sum(x * int(t) for x, t in zip([3600, 60, 1], timetmp.split(":")))
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
        'query': 'query getVideo($slug: String) {\n  getTVOOrgVideo(slug: $slug) {\n    uuid\n    nid\n    isSingle\n    tvoOriginal\n    nodeUrl\n    assetUrl\n    thumbnail\n    title\n    airingTime\n    broadcastRating\n    contentCategory\n    isDoNotDisplayRelatedContent\n    mostRecentOptOut\n    firstAiringTime\n    publishedAt\n    ageGroups\n    telescopeAssetId\n    hasCC\n    hasDV\n    openInNewWindow\n    metaTags\n    videoSource {\n      brightcoveRefId\n      dvBrightcoveRefId\n      __typename\n    }\n    program {\n      uuid\n      nodeUrl\n      title\n      isAppearInAllRelatedVideos\n      promotion\n      featuredImage\n      isInvisible\n      metaTags\n      notAvailableMsg\n      openInNewWindow\n      description\n      summary\n      coverImage\n      telescopeAssetId\n      imageAlt\n      __typename\n    }\n    programOrder\n    relatedContentLink\n    relatedProgramTitle\n    season\n    strand\n    tags\n    tagLinks\n    description\n    summary\n    episode\n    transcript\n    length\n    __typename\n  }\n}\n',
      }
      response = requests.post(URL_GRAPHQL_SERVER, headers=HEADERS, json=json_data)
      movie_js = json.loads(response.text)
 
      dtl = movie_js["data"]["getTVOOrgVideo"]
      name    = dtl["title"]
      url     = dtl["nodeUrl"]
      thumb   = dtl["thumbnail"]
      plot    = dtl["description"]
      timetmp = dtl["length"]
      if timetmp.count(':') == 0:
        duration = timetmp
      else:
        if timetmp.count(':') == 1:
          timetmp = "0:" + timetmp
          # Calculate time in seconds
        duration = sum(x * int(t) for x, t in zip([3600, 60, 1], timetmp.split(":")))
      infoList= {'mediatype': 'movie',
                 'Title': name,
                 'Duration': duration,
                 'Plot': plot}
      ilist = self.addMenuItem(name, 'GV', ilist, url, thumb, thumb, infoList, isFolder=False)
      return(ilist)
 
  def getAddonVideo(self, url):
      json_data = {
        'operationName': 'getVideo',
        'variables': {
          'slug': url,
        },
        'query': 'query getVideo($slug: String) {\n  getTVOOrgVideo(slug: $slug) {\n    uuid\n    nid\n    isSingle\n    tvoOriginal\n    nodeUrl\n    assetUrl\n    thumbnail\n    title\n    airingTime\n    broadcastRating\n    contentCategory\n    isDoNotDisplayRelatedContent\n    mostRecentOptOut\n    firstAiringTime\n    publishedAt\n    ageGroups\n    telescopeAssetId\n    hasCC\n    hasDV\n    openInNewWindow\n    metaTags\n    videoSource {\n      brightcoveRefId\n      dvBrightcoveRefId\n      __typename\n    }\n    program {\n      uuid\n      nodeUrl\n      title\n      isAppearInAllRelatedVideos\n      promotion\n      featuredImage\n      isInvisible\n      metaTags\n      notAvailableMsg\n      openInNewWindow\n      description\n      summary\n      coverImage\n      telescopeAssetId\n      imageAlt\n      __typename\n    }\n    programOrder\n    relatedContentLink\n    relatedProgramTitle\n    season\n    strand\n    tags\n    tagLinks\n    description\n    summary\n    episode\n    transcript\n    length\n    __typename\n  }\n}\n',
      }
      response = requests.post(URL_GRAPHQL_SERVER, headers=HEADERS, json=json_data)
      video_js = json.loads(response.text)
 
      # Play video
      vidurl = video_js["data"]["getTVOOrgVideo"]["assetUrl"]
      if vidurl == '':
        return False
      liz = xbmcgui.ListItem(path=vidurl)
      xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)
 
