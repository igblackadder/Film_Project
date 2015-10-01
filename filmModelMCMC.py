'''A script for analyzing the wrangled data. The data is broken down by year. 
    For each year the data are modeled with parameters found by Markov Chain 
    Monte Carlo simulation. The results are written to results.csv'''
import pandas as pd
import numpy as np
from pymc import Normal, Gamma, deterministic, MCMC, Matplot, Lambda
import matplotlib.pyplot as plt
import codecs
import sys
DIRECTORY=sys.path[0]

#import the wrangled data
wrangledDf=pd.read_csv(DIRECTORY+'/film_wrangled.csv', encoding='utf-8')
#import the names of the countries
with codecs.open(DIRECTORY+'/cat2.txt', 'r', 'utf-8') as f:
    countries=f.readline()
    countries=np.array(countries.strip('\n').split(', '))


def film_model_by_year(year, group, sameList, diffList):
    
    '''A model for film runtimes. This function defines the model to be analyzed 
        by the Markov Chain Monte Carlo.
        
        The runtime is assumed to have a gaussian distribution. The mean of that 
        gaussian for each film is the sum of a global mean runtime plus a 
        deviation specific to the country in which that film was made.
        
        Thus if a film was made in the USA the mean runtime would be modeled as 
        mean= world_avg + USA_deviation
        
        Seperate deviations are used for films where the writer was also a 
        director and for those where they were not.
        
        Thus a film made in the USA where the writer also directed are modeled 
        as mean = world_avg + USA_same_deviation.
        
        If a film is made in more than one country then an average deviation is 
        found.
        
        Thus a film made in the USA  and India where no the writer and director 
        were not the same has a mean modeled as 
        mean=world_avg + (USA_different_deviation + India_different_deviation)/2
        
        The model ensures that the total deviation is zero by demanding that
        
            sum over all countries ([country]_same_num * [country]_same_deviation) = 0
            sum over all countries ([country]_different_num * [country]_different_deviation) = 0
        where [country]_same_num is the number of films where the writer also 
        directed from that country.
        
        Parameters
        ----------
        
        year: string
            the year in which the films to be analyzed were released
            
        group: dataframe
            a pandas dataframe of the films released. The dataframe should have 
            columns for 'length' to denote the runtime of the film, 'Overlap' 
            and 'nonOverlap' to denote whether one of the writers was also one 
            of the directors, and 'Cou_[country]' for each country that denotes 
            whether a film was produced in that country.
            
        sameList: list
            list of strings. This is the countries represented in the dataset 
            in which at least one movie was produced where the writer was also 
            the director.
            
        diffList: list
            list of strings. The countries in the dataset where at least one 
            movie was produced in which none of the directors were also writers.
        
        
        '''
    
    world = Normal(year+'_world', mu=np.log10(100.), tau=1./(0.25**2), value=np.log10(100.))
    
    partial_deviation = Normal(year+"_log10_partialdev", mu=0, tau=1./(0.25**2), size = len(sameList)+len(diffList)-1, value=np.zeros(len(sameList)+len(diffList)-1))#, value=np.zeros(2*(len(countryList)+len(languageList)+len(genreList)))

    @deterministic
    def deviation(dev=partial_deviation, data=group):
        '''log10_deviations'''
        '''demand that the total deviation is 0 be making the final deviation
        equal to minus the weighted average of all the other deviations'''
        len_same_list=len(sameList)
        numSame=np.array([sum(data[u'Overlap']*data[u'Cou_'+country]) for country in sameList])
        numDiff=np.array([sum(data[u'nonOverlap']*data[u'Cou_'+country]) for country in diffList])
        final_deviation_value= (-1)*(sum(numSame * dev[:len_same_list]) + sum(numDiff[:-1] * dev[len_same_list:]))/numDiff[-1]
        dist=np.append(dev, final_deviation_value)
        return dist
        
    @deterministic
    def mu(a=world, dev=deviation, data=group):
        
        def get_deviations(same_list, diff_list, deviations, prefix, offset=0):
            tmp = np.zeros(len(data))
            same = pd.Series(tmp)
            diff = pd.Series(tmp)
            len_same_list=len(same_list)
            for i, deviation in enumerate(same_list):
                same=same.add(deviations[i + offset]*data[prefix+deviation].values)
            for i, deviation in enumerate(diff_list):
                diff = diff.add(deviations[i + len_same_list + offset]*data[prefix+deviation].values)
            same /= data[prefix+'TOTAL'].values
            diff /= data[prefix+'TOTAL'].values
            return data[u'Overlap'].values*same, data[u'nonOverlap'].values * diff
        
        country_same, country_diff = get_deviations(sameList, diffList, dev, u'Cou_', offset=0)
        return a + country_same + country_diff
    
    sigmaObs=Gamma(year+'_sigmaObs', alpha=1, beta=5)    
                
    obs = Normal(year+'_obs', mu=mu, tau=1./(sigmaObs**2), value=group[u'length'].values, observed=True)
    
    linear_deviation = Lambda(year+"_lindev", lambda x=world, y=deviation: 10.**(x+y) - 10.**(x))
    return locals()

def get_represented(df):
    '''Not every language or country is represented in every year of the
     dataset. Looking at only those that are substantially increases the speed 
     of the MCMC. The function returns a list of the countries. 
     
     Note that the retuned lists have the USA as their final entry. This allows 
     the MCMC to converge faster. That is because the model demands that the 
     total deviation is zero. To acheive this it 
     demands sum_over_all_countries([country]_num * [country]_deviation) = 0
     In practice, this equation is rearranged so that the last country listed 
     has it's deviation determined by 
     [last_country]_deviation = sum_over_other_countries([country]_num * [country]_deviation) / [last_country]_num
     Having the last country by one in which a large number of films are 
     represented in the dataset speeds the analysis.
        
        Parameters
        ----------
        
        df: dataframe
            a pandas dataframe of the films released. The dataframe should have
            columns for 'length' to denote the runtime of the film, 'Overlap' 
            and'nonOverlap' to denote whether one of the writers was also one of
            the directors, and 'Cou_[country]' for each country that denotes 
            whether a film was produced in that country.
            
        Returns
        -------
        
        dict:
            a dictionary with two entries, 'same' and 'diff'. 'same' is a list 
            of strings that represent the countries in which at least one movie 
            was produced where the writer was also the director. 'diff' is a 
            list of strings representing the countries where at least one movie 
            was produced in which none of the directors were also writers.
            '''
    tmpCounsSame=[]
    tmpCounsDiff=[]
    for country in countries:
        if (df[u'Overlap']*df[u'Cou_'+country]).any():
            tmpCounsSame.append(country)
        if (df[u'nonOverlap']*df[u'Cou_'+country]).any():
            tmpCounsDiff.append(country)
    tmpCounsDiff.remove(u'USA')
    tmpCounsDiff.append(u'USA')
    return {'same':tmpCounsSame, 'diff':tmpCounsDiff}


def writeStats(stats, sameCategories, diffCategories, sameN, diffN, year):
    '''After the MCMC is performed, the results are saved to a csv file.
        The values written to the file are the year, the country, whether the 
        deviation by this country is for writer and director being the same or 
        different, the number of films that were analyzed, the mean, the 
        standard deviation, the 95% lower limit and the 95% upper limit.
        
        Parameters
        ----------
        
        stats: dictionary
            a pymc stats dictionary of results
            
        sameCategories: list
            list of strings. This is the countries represented in the dataset
            in which at least one movie was produced where the writer was also
            the director.
            
        diffCategories: list
            list of strings. The countries in the dataset where at least one
            movie was produced in which none of the directors were also writers.
            
        sameN: list
            list of integeres. The number of films from each country in which 
            the writer was also the director
            
        diffN: list
            list of integeres. The number of films from each country in which 
            the writer was not the director
            
        year: integer
            the year in which the films analyzed were released
        
        '''
    with codecs.open('Desktop/results.csv', 'a', 'utf-8') as f:
        year=str(year)
        results = stats[year+'_world']
        worldlogMean = results['mean']
        worldlogSD = results['standard deviation']
        worldlog95Low = results['95% HPD interval'][0]
        worldlog95Hi = results['95% HPD interval'][1]
        worldlinMean = 10.**worldlogMean
        worldlinSD = 10.**worldlogSD
        worldlin95Low = 10.**worldlog95Low
        worldlin95Hi = 10.**worldlog95Hi
        num = sum(sameN)+sum(diffN)
        values=np.array([num, worldlinMean, worldlinSD, worldlin95Low, worldlin95Hi])
        values = map(str, values)
        entry=np.array([year, 'World', '-1'])
        entry = np.append(entry, values)
        f.write(','.join(entry) + '\n')
        for i, cat in enumerate(sameCategories+diffCategories):
            results = stats[year+'_lindev']
            linMean = results['mean'][i]
            linSD = results['standard deviation'][i]
            lin95Low = results['95% HPD interval'][0][i]
            lin95Hi = results['95% HPD interval'][1][i]
            Qsame = 'True' if i<len(sameCategories) else 'False'
            num = sameN[i] if i<len(sameCategories) else diffN[i-len(sameCategories)]
            values=np.array([num, linMean, linSD, lin95Low, lin95Hi])
            values = map(str, values)
            entry=np.array([year, cat, Qsame])
            entry = np.append(entry, values)
            f.write(','.join(entry) + '\n')
            
def initializeStats():
    '''Creates the file to which the MCMC results will be saved'''
    with codecs.open('Desktop/results.csv', 'a', 'utf-8') as f:
        entry=np.array(['date', 'category', 'QSame', 'number', 'linMean', 'linSD', 'lin95Low', 'lin95Hi'])#'logMean', 'logSD', 'log95Low', 'log95Hi',])
        f.write(','.join(entry) + '\n')

def dotheMCMC(x):
    '''Executes the Markov Chain Monte Carlo simulation. It enters a years worth
        of data into the model defined by the function film_model_by_year. Trial
        and error found that convergence occured with a total number of 300,000 
        iterations of the MCMC with a burn in of 75,000
        
        Parameters
        ----------
        
        x: list
            The list contains two elements. The first element is the year and 
            the second is a dataframe containing the data from all the films 
            released that year.
            
        Returns
        -------
        
        dictionary:
            stats: dictionary
                a pymc stats dictionary of results
                
            year: integer
                the year in which the analyzed films were analyzed
                
            group: dataframe
                pandas dataframe containing the data from all the films released
                that year
                
            sameList: list
                list of strings. This is the countries represented in the 
                dataset in which at least one movie was produced where the 
                writer was also the director.
                
            diffList: list
                list of strings. The countries in the dataset where at least one
                movie was produced in which none of the directors were also 
                writers.
            
            sameNum:list
                list of integeres. The number of films from each country in 
                which the writer was also the director
                
            diffNum: list
                list of integeres. The number of films from each country in 
                which the writer was not the director
        
        '''
    year, group =  x[0], x[1]
    tmpCountries = get_represented(group)
    tmpCountriesSame = tmpCountries['same']
    tmpCountriesDiff = tmpCountries['diff']
    numSame = [sum(group[u'Overlap'] * group[u'Cou_'+country]) for country in tmpCountriesSame]
    numDiff = [sum(group[u'nonOverlap'] * group[u'Cou_'+country]) for country in tmpCountriesDiff]
    mc=MCMC(film_model_by_year(str(year), group, tmpCountriesSame, tmpCountriesDiff))
    mc.sample(iter=300000, burn=75000, progress_bar=False)
    return {'stats':mc.stats(), 'year':year, 'group':group, 'sameList':tmpCountriesSame, 'diffList': tmpCountriesDiff, 'sameNum':numSame, 'diffNum': numDiff}



if __name__=='__main__':
    #group by year
    grp = wrangledDf.groupby('date')
    initializeStats()
    import multiprocessing as mp
    p=mp.Pool(processes=8)
    results = p.imap_unordered(dotheMCMC, grp)
    for res in results:
        mcStat = res['stats']
        year=res['year']
        group=res['group']
        tmpSame=res['sameList']
        tmpDiff=res['diffList']
        Num_same = res['sameNum']
        Num_diff = res['diffNum']
        #tmpLanguages=i['languages']
        #tmpGenres=i['genres']
        print year
        #update_plots(mcStat, year, group, tmpSame, tmpDiff)
        writeStats(mcStat, tmpSame, tmpDiff, Num_same, Num_diff, year)
    p.close()
    p.join() 
    plt.close('all')

