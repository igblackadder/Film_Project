'''A script for analysing film runtimes seperated based on whether or not the 
    scriptwriter was also the director. First the data is imported and a few 
    cuts made. Then a bayesian heirarchical model is specified. A Markov Chain 
    Monte Carlo simulation is produced and a plot of the results made.
    '''

import pandas as pd
import numpy as np
from pymc import MCMC, TruncatedNormal, Uniform, deterministic, Matplot
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d

#import data into a dataframe
df = pd.read_csv("film_data.txt", sep='\t', encoding='utf-8')
#drop duplcate data. The film may have been imported twice by the screen scraper
#or the film may be listed twice under two different imdb IDs.
df.drop_duplicates(subset=df.columns[1:], inplace=True)
df.drop(["title", "writer", "director"], axis=1, inplace=True)

#dropping films made before 1935 to exclude films from the silent era of cinema.
#dropping films made after 2004 because they are underrepresented in the first
#million entries on the internet movie database.
df = df[df["date"]>1935]
df = df[df["date"]<2005]

#We only want fictitious feature films so drop other genres.
df=df[['Adult' not in value for value in df["genre"]]]
df=df[['Documentary' not in value for value in df["genre"]]]
df=df[['Short' not in value for value in df["genre"]]]
df=df[['News' not in value for value in df["genre"]]]
#interestingly there are a small number of films mainly from the fifties that
#are described as talk-shows or game-shows. Clearly they should be dropped.
df=df[['Talk-Show' not in value for value in df["genre"]]]
df=df[['Game-Show' not in value for value in df["genre"]]]

df.sort("date", inplace=True)

#get lists of the different genres, languages and countries.
def get_unique(datafram, columnName):
    a = df[columnName]
    b = a.dropna()
    c=b.unique()
    d=np.array([item.split(',') for item in c])
    e=np.hstack(d)
    f=np.array([item.strip() for item in e])
    g=np.unique(f)
    return g

genres = get_unique(df, "genre")
languages = get_unique(df, "language")
countries = get_unique(df, "country")

#create dataframes that exclude films without language or country entries.
byCountry = df.dropna(subset=['country'])
byLanguage = df.dropna(subset=['language'])


def film_model_year(length, overlap, year_codes, num_years):
    '''Defines a heirarchical Bayesian model for the distribution of film 
        runtimes. The runtimes are modelled as a Normal distribution, the mean 
        of which is allowed to be different for different years and also for 
        when the writer is the director and when that's not the case. Those 
        means are themselves drawn from a normal distribution centered around 
        120 minutes but with a large standard deviation to keep the prior 
        suitably vauge. 
        
        Parameters
        ----------
        
        length: list
            The list of (integer or float) runtimes of movies
            
        overlap: list
            A list of booleans. Should be True if one of the writers was also 
            one of the directors. False otherwise
            
        year_codes: list
            A list of integers corresponding to the years in which the movies 
            were released
            
        num_years: integer
            Number of years spanned by the data
        '''
    # define hyper priors
    mu_a = TruncatedNormal('mu_a', mu=120, tau=1./(120**2), a=0, b=100000)
    tau = Uniform('tau', lower=0, upper=1000)
    
    # define priors
    means = TruncatedNormal('means', mu=mu_a, tau=tau, a=0, b=100000, size=2*num_years)
   
    #define mean that is allowed to be different for different years
    @deterministic
    def mu(means=means, x=overlap, y=year):
        return means[np.array(x)*num_years + y] 
    
    # define likelihood
    obs = TruncatedNormal('obs', mu=mu, tau=1./(5**2), a=0, b=100000, value=length, observed=True)
    return locals()


def film_year(length, overlap, date, title, iterations=240000, burn=160000):
    '''Performs a Markov Chain Monte Carlo simulation and produces a plot of the
        results
        
        Parameters
        ----------
        
        length: list
            The list of (integer or float) runtimes of movies
        
        overlap: list
            A list of booleans. Should be True if one of the writers was also
            one of the directors. False otherwise
        
        date: list
            A list of the years in which the movies were released
            
        title: string
            The title that will appear above the plot of the results
            
        iterations: integer
            The number of iterations to be performed by the Markov chain
            
        burn: integer
            the number of iterations of the Markov Chain that should be 
            discarded before analysis
            
        Returns
        -------
        
        results: dictionary
            The dictionary contains two elements: the results for when one of 
            the writers was also one of the directors ('same') and results for 
            when that was not the case ('diff'). Each of those entries is a 
            dictionary of the means of the distribution ('mean') and the 95% 
            confidence interval for the mean ('95%').
        
        '''
    #convert dates into codes
    num_years=len(set(date))
    years = pd.Categorical(date)
    year_codes = years.codes
    converter = {}
    for i in range(num_years):
        converter[i]=years.categories[i]
    
    #perform the MCMC simulation
    mc=MCMC(film_model_year(length, overlap, year_codes, num_years))
    mc.sample(iter=iterations, burn=burn)

    #Plot autocorrelation and related information to check that the MCMC has
    #converged and that the results are valid
    Matplot.plot(mc)

    #assemble the results
    diffMean,sameMean,diff95,same95={},{},{},{}
    for i in range(num_years):
        diffMean[converter[i]] = mc.means.stats()['mean'][i]
        sameMean[converter[i]] = mc.means.stats()['mean'][i+num_years]
        diff95[converter[i]] = mc.means.stats()['95% HPD interval'][:,i]
        same95[converter[i]] = mc.means.stats()['95% HPD interval'][:,i+num_years]
    results = {'diff':{'mean':diffMean, "95%":diff95}, 'same':{'mean':sameMean, "95%":same95}}

    #take the results and apply a cubic interpolation to the plots look nice
    #this in no way changes the results and is purely for aesthetic reasons
    x=converter.values()
    diffY = results['diff']['mean'].values()
    sameY = results['same']['mean'].values()
    diffInterp = interp1d(x, diffY, kind='cubic')#cubic
    sameInterp = interp1d(x, sameY, kind='cubic')
    xNew=np.linspace(min(x), max(x), 1000)
    diffY=diffInterp(xNew)
    sameY=sameInterp(xNew)
    
    diff95L = np.array(results['diff']['95%'].values())[:,0]
    diff95U = np.array(results['diff']['95%'].values())[:,1]
    
    same95L = np.array(results['same']['95%'].values())[:,0]
    same95U = np.array(results['same']['95%'].values())[:,1]
    
    diff95LInterp = interp1d(x, diff95L, kind='cubic')
    diff95UInterp = interp1d(x, diff95U, kind='cubic')
    same95LInterp = interp1d(x, same95L, kind='cubic')
    same95UInterp = interp1d(x, same95U, kind='cubic')
    
    diff95L = diff95LInterp(xNew)
    diff95U = diff95UInterp(xNew)
    same95L = same95LInterp(xNew)
    same95U = same95UInterp(xNew)

    #plot the results and dispay the figure.
    plt.figure(title,  figsize=(15,15))
    plt.title(title, fontsize=30)

    plt.plot(xNew, diffY, label='Diff', color='blue')
    plt.plot(xNew, sameY, label='Same', color='red')
    plt.legend(loc='best')

    plt.fill_between(xNew, diff95L, diff95U, color='blue', alpha=0.1)
    plt.fill_between(xNew, same95L, same95U, color='red', alpha=0.1)

    plt.xlabel('Year')
    plt.ylabel('Mean Runtime (minutes)')
    plt.show()
    plt.savefig(title + '.pdf')

    return results

def specifyData(name, type):
    '''Returns lists of the film lengths, whether one of the writers was also 
        one of the directors and the film realase dates. The function assumes 
        that the dataframes byCountry and byLanguage have already been specified
        
        Parameters
        ----------
        
        name: string
            The name of the desired subset of data. For example if films made in
            India are wanted then name would be 'India'
        
        type: string
            This should specify wether the name arguement is specifying a 
            language or a country
            
        Returns
        -------
        
        length: list
            a list of the film runtimes,
            
        overlap: list
            a list of booleans denoting whether or not films were directed by 
            someone who was also a scriptwriter for the movie
            
        date: list
            a list of the year in which the movies were released
        '''
    if type == 'country':
        data = byCountry[[name in country for country in byCountry['country']]]
    elif type == 'language':
        data = byLanguage[[name in language for language in byLanguage['language']]]
    length = data["length"]
    overlap = data["Wri/DirOverlap"]
    date = data["date"]
    return length.tolist(), overlap.tolist(), date.tolist()

#USA
USALength, USAOverlap, USADate = specifyData('USA', 'country')
film_year(USALength, USAOverlap, USADate, 'USA')
#India
IndiaLength, IndiaOverlap, IndiaDate = specifyData('India', 'country')
film_year(IndiaLength, IndiaOverlap, IndiaDate, 'India')
#Russian
RussianLength, RussianOverlap, RussianDate = specifyData('Russian', 'language')
film_year(RussianLength, RussianOverlap, RussianDate, 'Russian')
#Spanish
SpanishLength, SpanishOverlap, SpanishDate = specifyData('Spanish', 'language')
film_year(SpanishLength, SpanishOverlap, SpanishDate, 'Spanish')

