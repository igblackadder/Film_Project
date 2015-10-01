'''A script for plotting the results of the MCMC performed in the script filmModelMCMC.py 
    
    Error bar plots are created and a gaussian process is employed to find the 
    overall trend in the data
    
    '''

import pandas as pd
import codecs
import numpy as np
import matplotlib.pyplot as plt
from sklearn.gaussian_process import GaussianProcess
import sys

DIRECTORY = sys.path[0]


def plot_tool(data, title, col1, col2, folder):
    '''
        Creates an error bar plot possibly overlaid with a gaussian process line if there are more than 10 datapoints. The plot is saved in the given folder.
        
        Parameters
        ----------
        
        data: dataframe
            pandas dataframe containing 'date', 'linMean' wich is the average
            runtime and 95%errors in columns titled 'lin95Low' and 'lin95Hi'.
        
        title: string
            name of the plot
            
        col1: string
            the color of the plotted datapoints with errorbars
            
        col2: string
            the color of the gaussian process line
            
        folder: string
            the folder into which a pdf of the plot is to be saved
        
        '''
    print title
    plt.figure(title, figsize=(13, 6))
    plt.title(title, fontsize=30)
    plot_data(data, title, col1, folder)
    Year = np.array(j[u'date'].tolist())
    Mean = np.array(j[u'linMean'].tolist())
    SD = np.array(j[u'linSD'].tolist())
    if len(Year)>10:
        plot_gaussian(Year, Mean, SD, title, col2, folder)
    
    plt.xlim(1903, 2025)
    plt.xlabel('Year', fontsize=25)
    plt.ylabel('Minutes', fontsize=25)
    plt.xticks(fontsize = 20)
    plt.yticks(fontsize = 20)
    plt.subplots_adjust(left=0.10, bottom=0.18, top=0.90, right=0.95, wspace=0, hspace=0)
    if title != 'Undeviated Average':
        plt.ylim(-100, 100)
    plt.savefig(folder +'/'+title+'.pdf')

def plot_data(data, name, col, folder):
    '''
        plots data with errorbars and adds a legend
        
        Parameters
        -------
        
        data: dataframe
            pandas dataframe containing 'date', 'linMean' wich is the average 
            runtime and 95%errors in columns titled 'lin95Low' and 'lin95Hi'.
            
        name: string
            the title of the plot and the name under which the plot will be 
            saved.
            
        col: string
            the color of the plotted datapoints and errorbars
            
        folder: string
            the folder into which the pdf of the plot is to be saved
        '''
    year = data['date'].values
    mean = data['linMean'].values
    low = data['lin95Low'].values
    hi = data['lin95Hi'].values
    year = year+0.05 if col=='red' else year-0.05 if col=='blue' else year
    lowerBound = mean - low
    upperBound = hi - mean
    plt.errorbar(year, mean, yerr=[lowerBound,upperBound], fmt='.', color=col, capsize=0, lw=2, markersize=8)
    label='same' if col=='red' else 'diff' if col=='blue' else 'average'
    plt.plot ([],[],color=col,linewidth=3,label=label)
    plt.legend(loc=0, fontsize=24, ncol=2, frameon=False)
    plt.draw()


def plot_gaussian(x, y, ySD, name, col, folder):
    '''
        Performs a Gaussian process regression to find the trend in the data. The trend is then plotted (both best fit and 95% confidence interval) and a legend added.
        
        Parameters
        -------
        
        x: list
            integers corresponding to years. Must have the same length as y and ySD
            
        y: list
            the average runtime of films in each of the years specified in x. 
            
        ySD: list
            the standard deviation of the runtimes of films made in each of the years specified in x. 
        
        name: string
            the title of the plot and the name under which the plot will be saved.
            
        col: string
            the color of the plotted gaussian process regression line and error
            
        folder: string
            the folder into which the pdf of the plot is to be saved
        
        
        '''
    gp = GaussianProcess(corr='squared_exponential', theta0=1e-2,
                        thetaL=1e-9, thetaU=1e5,
                        nugget=(ySD) ** 2,
                        random_start=300)
    gp.fit(np.atleast_2d(x).T, np.atleast_2d(y).T)
    x_pred = np.atleast_2d(np.linspace(min(x)-2, max(x)+2, 1000)).T
    y_pred, MSE = gp.predict(x_pred, eval_MSE=True)
    x_pred=x_pred.ravel()
    y_pred=y_pred.ravel()
    sigma = np.sqrt(MSE)
    label='same ' if col=='yellow' else 'diff ' if col=='cyan' else ''
    plt.plot(x_pred, y_pred, col, label=label+'prediction')
    plt.fill_between(x_pred, (y_pred - 1.9600 * sigma), y2=(y_pred + 1.9600 * sigma), alpha=0.5, color=col, label=label+'95% confidence interval')
    plt.legend(loc=0, fontsize=24, ncol=2, frameon=False)
    plt.draw()

if __name__=='__main__':
    df=pd.read_csv(DIRECTORY + '/results.csv', encoding='utf-8')

    with codecs.open(DIRECTORY + '/categories.txt', 'r', 'utf-8') as f:
        countries=f.readline()
        countries=np.array(countries.strip('\n').split(', '))
        languages=f.readline()
        languages=np.array(languages.strip('\n').split(', '))
        genres=f.readline()
        genres=np.array(genres.strip('\n').split(', '))

    df.sort(columns='date', inplace=True)
    grp=df.groupby(('QSame', 'category'))#, 'date'))

    for i, j in grp:
        if i[1]=='World':
            plot_tool(j, 'Undeviated Average', 'green', 'magenta', DIRECTORY+'/plots')

        elif i[0]=='True':
            plot_tool(j, i[1], 'red', 'yellow', DIRECTORY+'/plots')
        else:
            plot_tool(j, i[1], 'blue', 'cyan', DIRECTORY+'/plots')
    plt.close('all')


