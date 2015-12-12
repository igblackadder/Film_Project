'''
    A script for analyzing the wrangled data. The data is broken down by year.
    For each year the data are modeled with parameters found by Markov Chain 
    Monte Carlo simulation. The results are written to results.csv The model is 
    defined in filmModel.py
    '''
from filmModel import *

import pandas as pd
import numpy as np
from pymc import MCMC
import codecs
import multiprocessing as mp
import sys
DIRECTORY=sys.path[0]

#import the wrangled data
wrangledDf=pd.read_csv(DIRECTORY+'/film_wrangled.csv', encoding='utf-8')
#import the names of the countries, languages and genres
with codecs.open(DIRECTORY+'/categories.txt', 'r', 'utf-8') as f:
    countries=f.readline()
    countries=np.array(countries.strip('\n').split(', '))
    languages=f.readline()
    languages=np.array(languages.strip('\n').split(', '))
    genres=f.readline()
    genres=np.array(genres.strip('\n').split(', '))


def initializeStats():
    '''Creates the CSV file in which the MCMC results will be saved. The file is 
        initialized with the headers:
        
        date – the year in which the analyzed films were released
        
        category – a country, language or genre. Can also be 'Global' to denote 
                    the undeviated average runtime
        
        QSame – whether or not the writer of the film was also the director. 
                 True if the writer was the director, False if not and -1 if the
                 category is 'Global'
        
        number – the number of films released in that category that year
        
        linMean – Either this is the average number of minutes by which films 
                   descibed by category differ from the global average in the 
                   given year or, if the category is 'Global', this is the 
                   average runtime of the movies in the analyzed year.
        
        linSD – the standard deviation for the mean given in linMean
        
        lin95Low – the 95% lower confidence bound for the mean given in linMean
        
        lin95Hi – the 95% upper confidence bound for the mean given in linMean
        
        '''
    entry=np.array(['date', 'category', 'QSame', 'number', 'linMean', 'linSD', \
                    'lin95Low', 'lin95Hi'])
    with codecs.open('Desktop/results.csv', 'a', 'utf-8') as f:
        f.write(','.join(entry) + '\n')

def writeStats(stats, countrySame, countryDiff, languageSame, languageDiff, \
               genreSame, genreDiff, year, totalNumber):
    '''
        writes the results of the MCMC analysis to the file results.csv
        
        Parameters
        ----------
        
        stats: a pyMC2 stats dictionary
            this contains the results of the MCMC, i.e. the average, standard 
            deviation and 95% confidence interval for each category and for the 
            global average.
        
        countrySame: array
            Contains an array of two element lists. Each pair is the name of a 
            country and the number of films made in that country in the given 
            year when the writer was also the director. The array is ordered by 
            the number of appearances from smallest to largest which is the same 
            as the order used in stats.
        
        countryDiff: array
            as countrySame but for when the writer was not the director
        
        langaugeSame: array
            as countrySame but for the language in which the films were made
        
        langaugeDiff: array
            as langaugeSame but for when the writer was not the director
        
        genreSame: array
            as countrySame but for the genre
        
        genreDiff: array
            as genreSame but for when the writer was not the director
        
        year: integer or string
            the year in which the analyzed movies were made
        
        totalNumber: integer
            the total number of movies released that year
        
        
        '''
    with codecs.open(u'/Users/gordonblackadder/Desktop/resultsTEST1.csv', 'a', \
                     'utf-8') as f:
        #write global average results to file
        year=str(year)
        results = stats[year+'_global']
        worldlinMean = str(10.**results['mean'])
        worldlinSD = str(10.**results['standard deviation'])
        worldlin95Low = str(10.**results['95% HPD interval'][0])
        worldlin95Hi = str(10.**results['95% HPD interval'][1])
        entry=np.array([year, 'Global', '-1', str(totalNumber), worldlinMean, \
                        worldlinSD, worldlin95Low, worldlin95Hi])
        f.write(','.join(entry) + '\n')
        
        #write each deviation result to file, category by category
        offset = 0 #first position of category in stats dictionary
        same = True #label whether writer was also the director
        for category in [countrySame, countryDiff, languageSame, languageDiff, \
                         genreSame, genreDiff]:
            writeStatsCategory(f, stats, offset, year, category, str(same))
            offset = offset + len(category)
            same = not same

def writeStatsCategory(file, data, offset, year, category, overlap):
    '''
        A helper function called by writeStats. This writes the results of MCMC 
        analysis for a particular category
        
        Parameters
        ----------
        
        file: filestream
            the file to which the results are to be written
        
        data: a pyMC2 stats dictionary
            this contains the results of the MCMC, i.e. the average, standard
            deviation and 95% confidence interval for each category and for the
            global average.
        
        offset: integer
            the first position of the results stored in the data dictionary 
            corresponding to the category
        
        year: string
            the year in which the films were released
        
        category: array like 
            the entries in the category, could be countries, languages or genres
        
        overlap: bool
            whether or not the writer of the film was also the director. True if
            the writer was the director, False if not
        
        '''
    for i in range(len(category)):
        position = offset+i #get position of the entry in the data dictionary
        finding = data[year+'_linDev']
        mean = str(finding['mean'][position])
        SD = str(finding['standard deviation'][position])
        low95 = str(finding['95% HPD interval'][0][position])
        hi95 = str(finding['95% HPD interval'][1][position])
        entry = np.array([year, category[i][0], overlap, category[i][1], mean, \
                          SD, low95, hi95])
        file.write(','.join(entry) + '\n')
            


def get_represented(df, category, prefix):
    '''
        A category such as language can have a very large number of of possible 
        entries, not all of which may appear in df. This function finds which 
        entries in a category appear in a dataframe for both when the writer was
        also the director and when they wre not.
        
        Parameters
        ----------
        
        df: dataframe
            a pandas dataframe of the films released. The dataframe should have
            columns for 'length' to denote the log_10 of the runtime of the
            film, 'Overlap' and 'nonOverlap' to denote whether one of the
            writers was also one of the directors, and 'Cou_[country]' for each
            country that denotes whether a film was produced in that country.
        
        category: list of strings
            all the possible entries in the df for a specific category, e.g. a 
            list of all film genres
        
        prefix: string
            the string appearing in the column names of df that descibe entries 
            in the category, e.g. 'Gen_' when the category is genre
        
        Returns
        -------
        
        dict: dictionary of arrays
            a dictionary of two elements: "same" and "diff". dict['same'] and
            dict['diff'] each contain an array of two element lists. Each pair 
            is the name of an entry in the category and the number of times that 
            entry appears in the df dataframe for overlapping and 
            non-overlapping writer/director respectively. The array is ordered 
            by the number of appearances from smallest to largest.
        
        '''
    #define the function used to order the array of entries
    sort_by_num_produced =lambda x,y: 1 if x[1]>y[1] else -1 if x[1]<y[1] else 0
    #find the represented entries and then order them
    Same = [[item, (df[prefix+item]*df[u'Overlap']).sum()] for item in category]
    Same = [x for x in Same if x[1]>0]
    Same.sort(cmp=sort_by_num_produced)
    #repeat for diff
    Diff = [[item, (df[prefix+item]*df[u'nonOverlap']).sum()] \
            for item in category]
    Diff = [x for x in Diff if x[1]>0]
    Diff.sort(cmp=sort_by_num_produced)
    return {'same':np.array(Same), 'diff':np.array(Diff)}

def dotheMCMC(x):
    '''
        Performs the Markov Chain Monte Carlo analysis to find the global 
        average of film runtimes and the deviation from that average for 
        different countries, languages and genres.
        
        Parameters
        ----------
        
        x: tuple
            x[0]: integer
                the year in which the films to be analysed were released.
        
            x[1]: pandas dataframe
                the dataframe containing all the movies released that year
        
        
        Returns
        -------
        
        stats: a pyMC2 stats dictionary
            this contains the results of the MCMC, i.e. the average, standard
            deviation and 95% confidence interval for each category and for the
            global average.
        
        group: pandas dataframe
            identical to the dataframe x[1]
        
        representedCountries: dictionary of arrays
            a dictionary of two elements: "same" and "diff". dict['same'] and
            dict['diff'] each contains an array of two element lists. Each
            pair is the name of a country and the number of times that country
            appears in the group dataframe for overlapping and non-overlapping
            writer/director respectively. The array is ordered by the number of
            appearances from smallest to largest.
        
        representedLanguages: dictionary of arrays
            as representedCountries but for languages
        
        representedGenres: dictionary of arrays
        as representedCountries but for genres
        
        numRepresented: integer
            the total number of movies released that year
        
        '''
    #get the parameters needed to initialize the model
    year, group =  x[0], x[1]
    representedCountries = get_represented(group, countries, 'Cou_')
    representedLanguages = get_represented(group, languages, 'Lan_')
    representedGenres = get_represented(group, genres, 'Gen_')
    
    numRepresented = representedCountries['same'].shape[0] + \
                        representedCountries['diff'].shape[0]
    numRepresented += representedLanguages['same'].shape[0] + \
                        representedLanguages['diff'].shape[0]
    numRepresented += representedGenres['same'].shape[0] + \
                        representedGenres['diff'].shape[0]
    
    #initialize the model in a pyMC object, then perform the MCMC
    mc=MCMC(film_model_by_year(str(year), group, representedCountries, \
                               representedLanguages, representedGenres, \
                               numRepresented))
    mc.sample(iter=300000, burn=75000, progress_bar=False)
    
    return {'stats':mc.stats(), 'year':year, 'countries':representedCountries, \
            'languages': representedLanguages, 'genres':representedGenres, \
            'num': numRepresented}



if __name__=='__main__':
    #group by year
    grp = wrangledDf.groupby('date')
    initializeStats()
    
    #perform the analysis of films released in different years in parallel
    #the results of the analysis are written to results.csv by writeStats()
    p=mp.Pool(processes=4)
    results = p.imap_unordered(dotheMCMC, grp)
    #as each result becomes available, write them to file
    for res in results:
        mcStat = res['stats']
        year = res['year']
        couSame = res['countries']['same']
        couDiff =res['countries']['diff']
        lanSame = res['languages']['same']
        lanDiff =res['languages']['diff']
        genSame = res['genres']['same']
        genDiff =res['genres']['diff']
        num = res['num']
        
        writeStats(mcStat, couSame, couDiff, lanSame, lanDiff, genSame, \
                   genDiff, year, num)
    p.close()
    p.join()

