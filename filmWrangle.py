'''when executed, this script reads the raw data written by the web scraper and 
    writes two new files. The first file is a comma seperated file containing 
    data on all the films in the analysis. The second is a text file containing 
    a list of all the countries, languages and genres that are represented in 
    the data.'''
import pandas as pd
import numpy as np
from string import split
import codecs
import sys
DIRECTORY = sys.path[0]

#import data
def get_clean_data():
    '''Returns a pandas data frame of the cleaned data. 
        The wrangling consists of 
            1) Dropping duplicate entries.

            2) Dropping undesired genres of film such as Short, Documentary and
                Adult (as the point of the analysis is to look at fiction 
                feature films).

            3) Some films in IMDB have incorrectly labeled languages or 
                countries. For example some films are listed as being made in 
                'Jerez de la Frontera' which is not an independent country but a
                part of Spain. These films are dropped.

            4) convert the column 'Wri/DirOverlap' into two columns of 1s and 0s
                that designate whether a film had a writer who was also a 
                director.
                Overlap = 1 when the film has a writer who was also a director
                Overlap = 0 when the film does NOT have a writer who was also a 
                director
                nonOverlap = 1 when the film does NOT have a writer who was also
                a director
                nonOverlap = 0 when the film has a writer who was also a 
                director

            5) Convert runtimes to log_10 runtimes
                
        Returns
        -------
        
        df: dataframe
            a pandas data frame containing the cleaned data
        '''
    #import the data
    df = pd.read_csv("Desktop/imdb_data.txt", sep='\t', encoding='utf-8')
    #drop duplcate data. The film may have been imported twice by the web scrape
    #or the film may be listed twice under two different imdb ids
    df.drop_duplicates(subset=df.columns[1:], inplace=True)
    df.drop(["title", "writer", "director"], axis=1, inplace=True)
    df = df[df["date"]<2015]
    #We only want fictitious feature films so drop other genres.
    #remove all reference to films with the following genres listed
    remove_references=lambda reference, column :df[[reference not in value for value in df[column]]]
    df = remove_references('Adult', 'genre')
    df = remove_references('Documentary', 'genre')
    df = remove_references('Short', 'genre')
    df = remove_references('News', 'genre')
    ##interestingly there are a small number of films mainly from the fifties that
    ##are described as talk-shows or game-shows. Clearly they should be dropped.
    df = remove_references('Talk-Show', 'genre')
    df = remove_references('Game-Show', 'genre')
    
    #drop entries that do not list a country or language
    df = df.dropna(subset=['country'])
    df = df.dropna(subset=['language'])
    df = df.dropna(subset=['genre'])
    
    #remove entries with incorrectly assigned countries
    df = remove_references(u'Jerez de la Frontera', 'country')#'Jerez de la Frontera' is in Spain and is not an independent country
    df = remove_references(u'La Pe\xf1uela country property', 'country')
    df = remove_references(u'New Line', 'country')
    df = remove_references(u'Official site [Italy]', 'country')
    df = remove_references(u'Official site [UK]', 'country')
    df = remove_references(u'Tottiekampu country', 'country')
    
    #remove entries with incorrectly assigned languages
    df = remove_references(u'Ancient (to 1453)', 'language')
    df = remove_references(u'Official site', 'language')
    df = remove_references(u'Old', 'language')
    df = remove_references(u'coffeeandlanguage.com General information [United States]', 'language')
    
    #convert the desciption of 'Wri/DirOverlap' into two columns of 1s and 0s
    df[u'Overlap']=df[u'Wri/DirOverlap'].astype(int)
    df[u'nonOverlap'] = (df[u'Wri/DirOverlap']+1)%2
    df.drop([u'Wri/DirOverlap'], axis=1, inplace=True)
    
    #order the dataframe by date
    df.sort(["date", "id"], inplace=True)
    df.reset_index(drop=True, inplace=True)
    
    #Film runtime is obviously a positive number menaing that the distribution
    #cannot be perfectly gaussian. Overcome this problem by converting runtimes
    #to log_10(runtimes)
    df['length'] = df['length'].map(np.log10)
    return df




#get lists of the different genres, languages and countries
def get_unique(dataframe, columnName):
    '''Returns a list of all the unique entries within a specified category. 
        For example if the category specified is 'Genre' then the list may 
        contain 'Action', 'Drama', 'Musical' etc.
        
        Parameters
        ----------
        
        dataframe: pandas dataframe
            the data frame containing a column entitled.
            
        columnName: string
            the name of a column appearing in dataframe. The entries in that 
            column are a comma sperated string. For example 'USA, UK, India'
            
        Returns
        -------
        
        f: list
            a list of strings of the unique entries counf in the column
        
        '''
    a = dataframe[columnName]
    b = a.dropna()
    c=b.unique()
    #note that the string containing the list is comma seperated
    d=np.array([item.split(', ') for item in c])
    e=np.hstack(d)
    f=np.unique(e)
    return f


#create column for each gene, language and country
def add_category_columns(df, fromCol, newCols, prefix):
    '''Instead of giving a list of countries, languages and genres associated 
        with each film, columns are added that correspond to each country, 
        language and genre. 1 means the film was made in the corresponding 
        country, in the corresponding language or within the corresponding 
        genre. 0 otherwise
        
        Parameters
        ----------
        
        df: pandas dataframe
            The dataframe to which the columns are to be added
            
        fromCol: string
            Name of the column containing a comma seperated string. For example
            'USA, UK, India'
            
        newCols: list
            a list of strings which are the names of the new columns e.g. 'USA'
            
        prefix: string
            each new column name will be prefixed with this string
            
        '''
    #create a new column called prefix+column e.g. Cou_USA
    #if column appears in the fromCol then enter 1 else enter 0
    # eg if 'USA' appears in the fromCol entry 'USA, UK, India' then Cou_USA is 
    # 1 else it is 0
    for column in newCols:
        tmp = lambda x: int(column in split(x, ', '))
        df[prefix+column] = df[fromCol].map(tmp)
    #get rid of the fromCol
    df.drop([fromCol], axis=1, inplace=True)
    df[prefix+newCols[0]] = df[prefix+newCols[0]].astype(float)
    #create a column with the total number of entries, e.g. is fromCol was 
    #'USA, UK, India' then the total is 3
    df[prefix + u'TOTAL'] = df[prefix+newCols[0]]
    for i in range(1, len(newCols)):
        df[prefix+newCols[i]] = df[prefix+newCols[i]].astype(float)
        df[prefix + u'TOTAL'] += df[prefix+newCols[i]]


if __name__ == '__main__':
    print 'Wrangling data'
    raw=get_clean_data()
    #get a list of all the countries, languages and genres
    countries = get_unique(raw, "country")
    languages = get_unique(raw, "language")
    genres = get_unique(raw, "genre")

    #add columns for each country, language and genre
    print "adding country columns"
    add_category_columns(raw, 'country', countries, u'Cou_')
    print "adding language columns"
    add_category_columns(raw, 'language', languages, u'Lan_')
    print "adding genre columns"
    add_category_columns(raw, 'genre', genres, u'Gen_')

    #write the munged data to a file
    print 'writing file'
    raw.to_csv(DIRECTORY+'/film_wrangled.csv', encoding='utf-8')

    #write the list of countries, languages and genres to a file
    with codecs.open(DIRECTORY + 'categories.txt', 'w', 'utf-8') as f:
        f.write(', '.join(countries) + '\n')
        f.write(', '.join(languages) + '\n')
        f.write(', '.join(genres) + '\n')

