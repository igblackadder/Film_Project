'''a script for accessing and analysing the first million entries listed on the 
    internet movie database website and gathering data on films into a 
    tab-seperated text file'''
from filmObtainItem import *
import os
import threading
from threading import Lock
import codecs
import time

def getFilm(i, screenLock, dataFile, dataLock, failFile, failLock):
    '''calls filmGrab and assesses whether film data was successfully obtained 
        or if the call failed. It then calls either the success of fail function

        Parameters
        ----------

        i: integer
            the IMDb id of the film for which access failed

        screenLock: semaphore
            a semaphore allowing the function to safely write to std out

        dataFile: file stream
            a file into which to store the retrieved data about the movie

        dataLock: semaphore
            a semaphore allowing the function to safely write to the dataFile

        failFile: file stream
            a file into which the fail message is written

        failLock: semaphore
            a semaphore allowing the function to safely write to the failFile

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

def fail(i, msg, screenLock, failFile, failLock):
    '''
    If aquiring data on a film with IMDb id i fails (perhaps because the entry 
        is actually a TV show, perhaps because the network connection timed out)
        this function prints the fail message msg and writes it in the failFile

        Parameters
        ----------

        i: integer
            the IMDb id of the film for which access failed

        msg: string
            a description of why the attempt to access the webpage failed

        screenLock: semaphore
            a semaphore allowing the function to safely write to std out

        failFile: file stream
            a file into which the fail message is written

        failLock: semaphore
            a semaphore allowing the function to safely write to the failFile
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

        Parameters
        ----------

        i: integer
            the IMDb id of the film that was successfully accessed

        filmObj: filmGrab object
            the object contains attributes about the accessed movie. Those 
            attributes are the date, name, the length of the movie, the 
            countries that the film was made in, the languages spoken in the 
            movie, the genres describing the movie, the writers, the directors 
            and whether one of the listed writers was also one of the listed 
            directors

        screenLock: semaphore
            a semaphore allowing the function to safely write to std out

        dataFile: file stream
            a file into which to store the retrieved data about the movie

        dataLock: semaphore
            a semaphore allowing the function to safely write to the dataFile
        
        '''
    #get attributes from object, create output string containing the films data
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

def main():
    '''Accesses webpages from the internet movie database corresponding to films
        and TV shows with IMDB ids from 1 to 1million. It does this in 
        increments with five second intervals to avoid accessing too many pages 
        at once. Creates files for successfully obtained data to be written to 
        along with a fail file to list failed attepts to access an entry so that
        they can be retried later.
        '''
    
    
    #create data file in which to store data about the movies
    datafilename = "Film_data"+".txt"
    if not os.path.isfile(datafilename):
        datafile = codecs.open(datafilename, mode='w', encoding='utf-8')
        header = "id\tdate\ttitle\tlength\tcountry\tlanguage\tgenre\twriter\tdirector\tWri/DirOverlap\n"
        datafile.write(header)
    else:
        datafile = codecs.open(datafilename, mode='a', encoding='utf-8')
      
    #create fail file in which to store information on IMDb entries that could 
    #not be accessed
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

    #create 200 threads at a time to access the first million entries
    stepsize = 200
    for j in range(1,1000001, stepsize):
        #instantiate the threads
        threads = [threading.Thread(target=getFilm, args=(i,lockScreenPrint, \
            datafile, lockDataFile, errorfile, lockErrorFile)) \
            for i in range(j,j+stepsize)]
        for thread in threads:
            thread.setDaemon(True)
        #start the threads
        for thread in threads:
            thread.start()
        #timeout the thread after 3 seconds
        for thread in threads:
            thread.join(3.)
        #register that the thread has failed if it has not yet returned
        for i in range(0, stepsize):
            if threads[i].isAlive():
                fail(i+j, "ThreadTimeout", lockScreenPrint, errorfile, \
                    lockErrorFile)
        #ensure that the system does not get overloaded by inserting a pause
        time.sleep(5)
    return 0


if __name__ == '__main__':
    main()
