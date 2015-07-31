'''a script for accessing and analysing the first million entries listed on the 
    internet movie database website and gathering data on films into a 
    tab-seperated text file'''
from filmGrab import *
import os
import threading
from threading import Lock
import codecs
import time

def fail(i, msg, screenLock, failFile, failLock):
    '''If aquiring data on a film with IMDB id i fails (perhaps because the entry is
        actually a TV show, perhaps because the network connection timed out) 
        this function prints the fail message msg and writes it in the failFile
        '''
    failTxt = str(i) + "\t" + msg
    failLock.acquire()
    failFile.write(failTxt + "\n")
    failLock.release()
    screenLock.acquire()
    print failTxt
    screenLock.release()


def success(i, filmObj, screenLock, dataFile, dataLock):
    '''If aquiring the data on a film with IMDB id i is successful then the 
        films data (id number, date, title, runtime, country of origin, 
        languages, genres, writers, directors and whether one of the 
        scriptwriters was also the director) is printed and written to the data 
        text file in the tab-seperated variables format. NOTE tab-seperated 
        variables chosen because film titles sometimes have have a comma and to 
        allow a comma seperated list of the films languages, countries, genres, 
        writers and directors.
        '''
    country = ', '.join(filmObj.country)
    language = ', '.join(filmObj.language)
    writer = ', '.join(filmObj.writer)
    director = ', '.join(filmObj.director)
    genre = ', '.join(filmObj.genre)
    textout = "%d\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" %(i, filmObj.date, filmObj.name, str(filmObj.time), country, language, genre, writer, director, filmObj.same)

    screenLock.acquire()
    print textout
    screenLock.release()

    dataLock.acquire()
    dataFile.write(textout)
    dataLock.release()


def doFilm(i, screenLock, dataFile, dataLock, failFile, failLock):
    '''calls filmGrab and assesses whether film data was successfully obtained 
        or if the call failed. It then calls either the success of fail function
        '''
    film = filmGrab(i)
    screenLock.acquire()
    print str(i)
    screenLock.release()
    if film.failed:
        if film.state != "NA":
            fail(i, film.state, screenLock, failFile, failLock)
    else:
        success(i, film, screenLock, dataFile, dataLock)


def main():
    '''Accesses webpages from the internet movie database corresponding to films
        and TV shows with IMDB ids from 1 to 1million. It does this in 
        increments with five second intervals to avoid accessing too many pages 
        at once. Creates files for successfully obtained data to be written to 
        along with a fail file to list failed attepts to access an entry so that
        they can be retried later.
        '''
    stepsize = 200
    
    #create data file and fail file
    datafilename = "Film_data"+".txt"
    if not os.path.isfile(datafilename):
        datafile = codecs.open(datafilename, mode='w', encoding='utf-8')
        header = "id\tdate\ttitle\tlength\tcountry\tlanguage\tgenre\twriter\tdirector\tWri/DirOverlap\n"
        datafile.write(header)
    else:
        datafile = codecs.open(datafilename, mode='a', encoding='utf-8')
        
    errorfilename = "Film_fail"+".txt"
    if not os.path.isfile(errorfilename):
        errorfile = codecs.open(errorfilename, mode='w', encoding='utf-8')
        header = "id\terror\n"
        errorfile.write(header)
    else:
        errorfile = codecs.open(errorfilename, mode='a', encoding='utf-8')
    
    #create locks to ensure that only one film prints to screen or to a file at
    #a given time.
    lockScreenPrint = Lock()
    lockDataFile = Lock()
    lockErrorFile = Lock()

    #create threads to access the first million entries
    for j in range(1,1000001, stepsize):
        threads = [threading.Thread(target=doFilm, args=(i,lockScreenPrint, datafile, lockDataFile, errorfile, lockErrorFile)) for i in range(j,j+stepsize)]
        for thread in threads:
            thread.setDaemon(True)
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(3.)#timeout the thread after 3 seconds
        for i in range(0, stepsize):
            if threads[i].isAlive():
                fail(i+j, "ThreadTimeout", lockScreenPrint, errorfile, lockErrorFile)
        time.sleep(5)
    return 2000001


if __name__ == '__main__':
    main()
