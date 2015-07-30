'''Defines the class filmGrab for getting data on films from the website 
    of the Internet Movie Database'''

import numpy as np
import bs4 as bs4
import requests
from requests.exceptions import ConnectionError
from requests.exceptions import Timeout
from requests.exceptions import HTTPError
import socket
import re
from retrying import retry, RetryError

def retry_if_timeout_or_connection_error(exception):
    '''Return True if the program should try accessing the requested webpage
        again. In this case True if there is a TimeoutError or a ConnectionError
        '''
    return isinstance(exception, Timeout) or isinstance(exception, ConnectionError)

class filmGrab():
    '''
    filmGrab(num)
    
    Get data about a film from www (dot) IMDB (dot) com
    
    Parameters
    ----------
    
    num: integer
        positive integer between 1 and 5million.
        This number is the imdb id number for an entry on their website.
        For example num=1 corresponds to the entry for a short film from 1984 
        called 'Carmencita.'
    
    Attributes
    ----------
    
    failed: boolean
        True if there was a problem accessing the webpage or if the page did not
        contain information on a film (most imdb entries are tv shows)
        False otherwise
    
    state: string
        If failed is False then the state will be "all data gained."
        If failed is True then state will be the reason for that fail. Possible 
        states include that, after five attempts, a connection could not be made
        to the webpage or the http request timed out, in which case the state 
        would be "timeoutOrConnenction." If there is an HTTP request error, such
        as page not found, then the error code is returned, eg "404." And if the
        webpage did not contain data on a film, or if there was pertinent data 
        missing, then state will be "NA."
    
    date: string
        If failed=False, this is the year the film was released.
        
    name: string
        If failed=False, this is the title of the film.
        
    time: float
        If failed=False, this is the runtime of the movie
        
    country: string
        If failed=False, this is the country or countries in which the film was 
        made. If there are several countries then they are seperated by commas.
        
    language: string
        If failed=False, this is the language or languages used in the film. If
        there are several languages then they are seperated by commas.
        
    genre: string
        If failed=False, this is the genre or genres that imdb use to descibe
        the film. If there are several genres then they are seperated by commas.
        
    writer: string
        If failed=False, this is the writer or writers associated with the film. 
        If there are several writers then they are seperated by commas.
        
    director: string
        If failed=False, this is the director or directors associated with the 
        film. If there are several directors then they are seperated by commas.
        
    same: boolean
        If failed=False, this is True if the name of a one of the writers is the 
        same as one of the names of the directors
        
    Notes
    -----
    
    There are currently between 4 and 5 million entries on the internet movie 
    database, most of which are episodes of TV shows.
    
    '''
    def __init__(self, idnum):
        self.idnum=idnum
        self.failed = False
        self.state = "Empty"
        urlPrim = "http://www.imdb.com/title/tt" + str(self.idnum)+"/"
        urlSec = urlPrim + "fullcredits"
        primaryPage = self._getPage(urlPrim)
        self._getPrimaryData(primaryPage)
        secondaryPage = self._getPage(urlSec)
        self._getSecondaryData(secondaryPage)
    
    #retries up to 5 times when there are timeout errors, with a 0.5 second gap
    #between tries
    @retry(stop='stop_after_attempt', stop_max_attempt_number=5,
           wait='fixed_sleep', wait_fixed=500,
           retry_on_exception=retry_if_timeout_or_connection_error)
    def _getPageInt(self, address):
        if self.failed == True:
            return
        try:
            page=requests.get(address, timeout = 5)
        except socket.timeout:
            raise Timeout
        except Timeout:
            raise Timeout
        except ConnectionError:
            raise ConnectionError
#            return self._fail("ConnectionError")
        except socket.error:
            return self._fail("socket error")
        except HTTPError as e:
            return self._fail(e.response.statuscode)
        except KeyboardInterrupt:
            raise
        except Exception as inst:
            return self._fail("Unknown Exception:" + str(type(inst))+"+"+str(inst.args)+"+"+str(inst))
        except:
            return self._fail("Unknown Error")
        else:
            if page.status_code != 200:
                return self._fail(str(page.status_code))
            self.state = "Page " + address + " Accessed"  
            return bs4.BeautifulSoup(page.text)
    #wrapper for _getPageInt(). Once getPageInt() has retried 5 times
    #unsuccessfully, then the wrapper executes the _fail() method
    def _getPage(self, address):
        try:
            page=self._getPageInt(address)
        except RetryError:
            return self._fail("timeoutOrConnenction")
        return page

    # gets data from www.imdb.com/title/tt<num> on whether or not the entry is a
    #tv program or video. If not then it gets the title, the date, the runtime,
    #the countries, the languages and the genres
    def _getPrimaryData(self, primaryPage):
        if self.failed == True:
            return
        #check if page is for a tv show or video
        try:
            medium=primaryPage.find("div", {"class": "infobar"})
        except AttributeError:
            return self._fail("NA")
        except Exception as inst:
            return self._fail("Unknown Error:" + str(type(inst))+"+"+str(inst.args)+"+"+str(inst))
        TVRX = re.compile("TV")
        VidRX = re.compile("Video")
        if TVRX.search(medium.decode()) != None or VidRX.search(medium.decode()) != None:
            return self._fail("NA")

        #get the name of the movie
        try:
            getName = primaryPage.h1.find("span", {"itemprop":"name"})
        except AttributeError:
            return self._fail("NA")
        except Exception as inst:
            return self._fail("Unknown Error:" + str(type(inst))+"+"+str(inst.args)+"+"+str(inst))
        if getName == None:
            return self._fail("Couldn't find name and date")
        self.name = getName.contents[0].strip()
        
        #get the date the movie was released
        try:
            self.date = primaryPage.h1.find("a").contents[0]
        except AttributeError:
            return self._fail("NA")
        except Exception as inst:
            return self._fail("Unknown Error:" + str(type(inst))+"+"+str(inst.args)+"+"+str(inst))

        #get the runtime of the movie in minutes
        #the RegEx below looks for digits, possibly a thousands seperator then
        #possibly more digits, possibly a decimal point and possible more digits
        timeRX=re.compile('\d+[,]*\d*[\.]*\d*'
        try:
            getTime = primaryPage.find("time", {"itemprop":"duration"})
        except AttributeError:
            return self._fail("NA")
        except Exception as inst:
            return self._fail("Unknown Error:" + str(type(inst))+"+"+str(inst.args)+"+"+str(inst))
        if getTime == None:
            return self._fail("NA")
        timeSearch=getTime.contents[0]
        timeString = timeRX.findall(timeSearch.decode())[0]
        self.time = float(timeString.replace(',', ''))

        #get the language(s) and country(ies) of the movie
        try:
            details = primaryPage.find("div", {"class":"article", "id":"titleDetails"}).find_all("a")
        except AttributeError:
            return self._fail("NA")
        except Exception as inst:
            return self._fail("Unknown Error:" + str(type(inst))+"+"+str(inst.args)+"+"+str(inst))
        self.country=[]
        self.language=[]
        wordCount = re.compile("country")
        wordLang = re.compile("language")
        for detail in details:
            if detail.attrs["href"] !=None:
                if wordCount.search(detail.attrs["href"]):
                    self.country.append(detail.contents[0].strip())
                if wordLang.search(detail.attrs["href"]):
                    self.language.append(detail.contents[0].strip())
        
        #get the genre(s)
        self.genre=[]
        try:
            genreSearch = primaryPage.find("div", {"itemprop":"genre"})
        except AttributeError:
            return self._fail("NA")
        except Exception as inst:
            return self._fail("Unknown Error:" + str(type(inst))+"+"+str(inst.args)+"+"+str(inst))
        if genreSearch == None:
          return self._fail("NA")
        for gen in genreSearch.find_all("a"):
            self.genre.append(gen.contents[0].strip())
        self.state = "Primary data gained"

    #gets data from www.imdb.com/title/tt<num>/fullcredits on the writers and
    #directors
    def _getSecondaryData(self, secondaryPage):
        if self.failed == True:
            return           
        self.director = []
        self.writer=[]   
        wordDir = re.compile("Directed")
        wordWri = re.compile("Writing") 
        wordCast = re.compile("Cast")
        #look for the list of credits
        try:
            credits=secondaryPage.find("div", {"id":"fullcredits_content", "class":"header"})
            tmp = credits.h4
        except AttributeError:
            return self._fail("NA")
        except Exception as inst:
            return self._fail("Unknown Error:" + str(type(inst))+"+"+str(inst.args)+"+"+str(inst))
        #cycle through the list of credits looking for the writing credits and
        #the directing credits
        while(tmp != None):
            if wordDir.search(tmp.contents[0]) != None:
                tmp = tmp.find_next_sibling()
                for name in tmp.find_all("td", {"class":"name"}):
                    self.director.append(name.a.contents[0].strip())
            if wordWri.search(tmp.contents[0]) != None:
                tmp = tmp.find_next_sibling()
                for name in tmp.find_all("td", {"class":"name"}):
                    self.writer.append(name.a.contents[0].strip()) 
            if wordCast.search(tmp.contents[0]) != None:
                break
            tmp = tmp.find_next_sibling() 
        if len(self.writer) == 0 or len(self.director)==0:
            return self._fail("NA")
        self.same = np.in1d(self.writer, self.director).any() 
        self.state = "all data gained"
        
    # sets the attribute failed to True and sets the state to msg.
    def _fail(self, msg):
        self.failed =True
        self.state = msg
        return True