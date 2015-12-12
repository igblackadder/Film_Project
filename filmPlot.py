'''
    A script for plotting the results of the MCMC performed in the script 
    filmMCMC.py
    
    Error bar plots are created and a gaussian process regression is employed to
    find the trend in the data.
    
    Plots are created for the global average of film runtimes and the deviations
    from that average for different categories. The categories are a set of 
    countries, languages and genres.
    
    '''

import pandas as pd
import codecs
import numpy as np
import matplotlib.pyplot as plt
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF
import sys

DIRECTORY = sys.path[0]

#import the results of the MCMC
df=pd.read_csv(DIRECTORY + '/results.csv', encoding='utf-8')
df.sort(columns='date', inplace=True)

#import the names of the countries, languages and genres
with codecs.open(DIRECTORY + '/categories.txt', 'r', 'utf-8') as f:
    countries=f.readline()
    countries=np.array(countries.strip('\n').split(', '))
    languages=f.readline()
    languages=np.array(languages.strip('\n').split(', '))
    genres=f.readline()
    genres=np.array(genres.strip('\n').split(', '))


def plot_tool(data, title, folder):
    '''
        Creates an error bar plot overlaid with the result of a gaussian process
        regression. This can be performed for the global average and for the 
        deviations from the average. The latter is only plotted if there is data
        for both writer/director overlap and non-overlap over at least 50 years 
        with 10 or more films in each year. This ensures that the gaussian 
        process regression is good and meaningful (this is quite conservative, 
        the effects of relaxing this should be explored).
        
        Parameters
        ----------
        
        data: dataframe
            pandas dataframe containing 'date' which is the year the films were 
            first released, 'QSame' which is True when one of the writers 
            directed the movie and False otherwise (and it is a sentinal value 
            of -1 when the category is the Global average), 'number' which are 
            the number of films released that year, 'linMean' which is the 
            average runtime of films that year and 95%errors in columns called 
            'lin95Low' and 'lin95Hi'.
        
        title: string
            category of the plotted data e.g. "Romance" or "French"
        
        folder: string
            the filepath into which the plots should be saved.
        
        '''
    plt.figure(title, figsize=(13, 6))
    plt.title(title, fontsize=30)
    
    if title == 'Global':
        plot_data(data, 'green', 'Global Average')
        plot_gaussian(data, 'green', 'Global Average')
    else:
        #seperate data into writer/director overlap and non-overlap
        #demand that the results for each year be based on at least 10 films
        same = data[(data.QSame == 'True') & (data.number>=10)]
        diff = data[(data.QSame == 'False') & (data.number>=10)]
        #demand that there must be at least fifty years worth of data
        min_years = 50
        if len(same)<min_years or len(diff)<min_years:
            plt.close()
            return
        #save plots to different subfolders depending on their category
        if title in countries:
            folder +='/countries'
        elif title in languages:
            folder += '/languages'
        else:
            folder += '/genres'
        plot_data(same, 'red', 'same')
        plot_data(diff, 'blue', 'different')
        
        plot_gaussian(same, 'red')
        plot_gaussian(diff, 'blue')
        
        plt.ylim(-60, 150)
    
    
    plt.xlim(1903, 2016)
    plt.xlabel('Year', fontsize=25)
    plt.ylabel('Minutes', fontsize=25)
    plt.xticks(fontsize = 20)
    plt.yticks(fontsize = 20)
    plt.subplots_adjust(left=0.10, bottom=0.18, top=0.90, right=0.95, \
                        wspace=0, hspace=0)
    
    plt.legend(loc='best', fontsize=24, ncol=1, frameon=False)
    plt.savefig(folder +'/'+title+'.pdf')
    plt.close()


def plot_data(data, col, label):
    '''
        Plots the results of the MCMC with errorbars
        
        Parameters
        ----------
        
        data: dataframe
            pandas dataframe containing 'date', 'linMean' which is the average
            runtime and 95%errors in columns called 'lin95Low' and 'lin95Hi'.
        
        col: string
            the color in which the plot the data
        
        label: string
            entry for the plots legend. If the data are from films where the 
            writer also directed then this could be 'same' otherwise is could be
            'different'
        '''
    
    #extract the results from the dataframe
    year = np.float64(data['date'].values)
    mean = data['linMean'].values
    low = data['lin95Low'].values
    hi = data['lin95Hi'].values
    # add some jitter in the x-dimension to clearly seperate same and diff
    # data points
    if label == 'same':
        year += .1
    elif label=='different':
        year -= .1
    #calculate the 95% interval
    lowerBound = mean - low
    upperBound = hi - mean
    
    plt.errorbar(year, mean, yerr=[lowerBound,upperBound], fmt='.', color=col, \
                 capsize=0, lw=2, markersize=8, alpha = 0.7)
    #add ledend
    plt.plot ([],[],color=col,linewidth=3,label=label)
    plt.legend(loc=0, fontsize=24, ncol=2, frameon=False)
    plt.draw()


def plot_gaussian(data, col):
    '''
        Plots the gaussian process regression with a characteristic length scale
        of 10 years. Essentially this highlights the 'slow trend' in the data.
        
        Parameters
        ----------
        
        data: dataframe
        pandas dataframe containing 'date', 'linMean' which is the average
        runtime and 'linSD' which is the standard deviation.
        
        col: string
        the color in which the plot the data
        '''
    #extract the results from the dataframe
    Year = np.array(data[u'date'].tolist())
    Mean = np.array(data[u'linMean'].tolist())
    SD = np.array(data[u'linSD'].tolist())
    
    #initialize the gaussian process. Note that the process is calculated with a
    #length scale of 10years to give the 'slow trend' in the results.
    length_scale = 10.
    kernel = 1.* RBF(length_scale)
    gp = GaussianProcessRegressor(kernel=kernel, sigma_squared_n=(SD) ** 2, \
                                  normalize_y=True)
    
    #now fit the data and get the predicted mean and standard deviation
    #Note: for reasons that are unclear, GaussianProcessRegressor won't take 1D
    #arrays so the data are converted to 2D and then converted back for plotting
    gp.fit(np.atleast_2d(Year).T, np.atleast_2d(Mean).T)
    Year_array = np.atleast_2d(np.linspace(min(Year)-2, max(Year)+2, 100)).T
    Mean_prediction, SD_prediction = gp.predict(Year_pred, return_std=True)
    Year_array=Year_array.ravel()
    Mean_prediction=Mean_prediction.ravel()
    
    #plot the predicted best fit
    plt.plot(Year_array, Mean_prediction, col, alpha=1)
    #plot the 95% confidence interval
    plt.fill_between(Year_array, (Mean_prediction - 1.9600 * SD_prediction), \
                     y2=(Mean_prediction + 1.9600 * SD_prediction), alpha=0.5, \
                     color=col)
    plt.draw()


if __name__=='__main__':
    grp=df.groupby('category')
    for name, categoryDF in grp:
        print name
        plot_tool(categoryDF, name, DIRECTORY+'/plots')

