'''A model for film runtimes. This function defines the model to be analyzed
    by the Markov Chain Monte Carlo module pyMC2.
    
    The model assumes that runtimes follow a Normal distribution. The mean
    of the distribution is allowed to vary by country, language, genre and
    whether the script writer was also the director. This is done by finding
    a global average and then deviations from that.
    
    Therefore the mean is:
    
    mean=global_mean+ (country_deviation+ language_deviation+ genre_deviation)/3
    
    where there is one set of country, language and genre deviations for
    when the writer was the director and a different set for when the writer
    was not the director.
    
    To ensure that the deviations are just that, the model demands that the 
    total deviation from the global average should be zero for each category of 
    deviation.
    
    SumOverCategory(category_deviation * number_of_films_in_category) = 0
    
    where category_number is the number of films in that category. Note that 
    this sum is over both deviations for overlap in the list of writers and 
    directors and no overlap.'''

import pandas as pd
import numpy as np
from pymc import Normal, Gamma, deterministic, MCMC, Matplot, Lambda

#some helper functions used in the model are defined at the bottom

#the model
def film_model_by_year(year, group, couDict, lanDict, genDict, numCategories):
        '''
        A model of film runtimes for analysis by PyMC2. Intended use:
        
        mc=MCMC(film_model_by_year(str(year), group, representedCountries, \
            representedLanguages, representedGenres, numRepresented))
        mc.sample(iter=300000, burn=75000, progress_bar=False)
        
        Parameters
        ----------
        
        year: string
            the year in which the films to be analyzed were released
        
        group: dataframe
            a pandas dataframe of the films released. The dataframe should have
            columns for 'length' to denote the log_10 of the runtime of the 
            film, 'Overlap' and 'nonOverlap' to denote whether one of the 
            writers was also one of the directors, and 'Cou_[country]' for each 
            country that denotes whether a film was produced in that country.
        
        couDict: dictionary
            a dictionary of two elements: "same" and "diff". couDict['same'] and
            couDict['diff'] each contain an array of two element lists. Each 
            pair is the name of a country and the number of times that country 
            appears in the group dataframe for overlapping and non-overlapping
            writer/director respectively. The array is ordered by the number of 
            appearances from smallest to largest.
            
        lanDict: dictionary
            as couDict but for languages contained in the dataframe group
            
        genDict: dictionary
            as couDict but for genres contained in the dataframe group
            
        numCategories: integer
            The total number of entries contained in couDict["same"] plus 
            couDict["diff"] plus the number of entries in "same" and "diff" for 
            each of lanDict and genDict.
            
        Returns
        -------
        
        This function is intented to be analysed by pyMC. It is therefore more 
            pertinent to look at the returns in the dictionary mc.stats() which 
            contain the results of the Markov Chain Monte Carlo analysis.
        
        mc.stats()["<year>_global"]
            The log_10 of the average runtime in minutes of all the movies in 
            group
            
        mc.stats()["<year>_linDev"]
            The average number of minutes (NOT log_10 minutes) by which each 
            categories average runtime differs from the global average runtime.
        
        '''
    #the log_10 average runtime of films modelled as a normal distribution
    globalAvg = Normal(year+'_global', mu=np.log10(100.), tau=1./(0.25**2), \
                       value=np.log10(100.))
            
    # create the deviations from that average for each country, language and
    #genre for both writer-director overlap and non-overlap. Assume that the
    #deviations are normally distributed. One deviation in each category
    #(country, language and genre) is left uninitiallized as its value must be
    #fixed to ensure 0 total deviation.
    category_deviation = Normal(year+'_log10_categoryDev', mu=0, \
                                tau=1./(0.25**2), size = numCategories-3, \
                                value=np.zeros(numCategories-3))
    
    @deterministic
    def deviation(dev=category_deviation):
        '''
        demand that the total deviation is 0 be making the final deviation in
        each category equal to minus the weighted average of all the other 
        deviations
        
        Parameters
        ----------
        
        dev: array like
            the log_10 deviation from the average runtime for films by category 
            (country, language and genre) for both writer-director overlap and 
            non-overlap. The list should contain the deviations for all but one 
            entry in each category.
        
        Returns
        -------
        
        array like
            the input list with three additional values inserted. The inserted 
            values are such that the total, weighted deviation in each category 
            is 0:
            '''

        #insert the final country deviation value
        dev = deviation_insert_val(dev, couDict, 0)
        #insert the final language deviation value
        offset = couDict['same'].shape[0]+couDict['diff'].shape[0]
        dev = deviation_insert_val(dev, lanDict, offset)
        #insert the final genre deviation value
        offset += lanDict['same'].shape[0] + LanDiffLen=lanDict['diff'].shape[0]
        dev = deviation_insert_val(dev, genDict, offset)
        
        return dev
    
    @deterministic
    def mu(a=globalAvg, dev=deviation):
        '''
            Calculates the mean associated with each film given its listed 
            country(ies), language(s), genre(s) and whether there is 
            writer-director overlap or non-overlap.
            
            A film is listed in the group dataframe as having been made in one 
            or more countries, in one or more languages and as fitting one or 
            more genres. Each of these descriptors has an associated deviation 
            from the global average and these deviations vary depending on 
            whether or not the writer was also the director.
            
            To get the deviation from the average associated with a particular 
            film, every deviation associated with the films descriptors are 
            added together and the total is divided by the number of 
            descriptors.
            
            The total average is obtained by adding this deviation to the global
            average
            '''
        #calculate the deviations for each film based on country...
        cou_same, cou_diff = get_deviations(couDict['same'][:,0], \
                                            couDict['diff'][:,0], dev, u'Cou_',\
                                            group, offset=0)
        
        #...then language...
        offset = couDict['same'].shape[0] + couDict['diff'].shape[0])
        lan_same, lan_diff = get_deviations(lanDict['same'][:,0], \
                                            lanDict['diff'][:,0],dev, u'Lan_', \
                                            group, offset=offset
        
        #...and finally by genre
        offset+=lanDict['same'].shape[0] + lanDict['diff'].shape[0]
        gen_same, gen_diff = get_deviations(genDict['same'][:,0], \
                                            genDict['diff'][:,0], dev, u'Gen_',\
                                            group, offset=offset)
        
        #then combine for the total predicted average.
        return a + (cou_same + cou_diff + lan_same + lan_diff \
                    + gen_same + gen_diff)/3.
    
    #model the standard deviation of the normal distribution of runtimes as a
    #gamma function
    sigmaObs=Gamma(year+'_sigmaObs', alpha=1, beta=5)
                                            
    # model the observed distribution of log_10 film runtimes as a normal
    #distribution with mean given by mu and standard deviation given by sigmaObs
    obs = Normal(year+'_obs', mu=mu, tau=1./(sigmaObs**2), \
                 value=group[u'length'].values, observed=True)
    
    # calculate the deviation from the average in minutes. 
    linear_deviation = Lambda(year+"_linDev", lambda x=globalAvg, y=deviation:\
                              10.**(x+y) - 10.**(x))
            
    return locals()



# define some helper functions to be used by the model
def deviation_insert_val(devArray, categoryDict, offset, sameLen, diffLen):
    '''FOR USE IN FILM_MODEL_BY_YEAR
        calculates the weighted average deviation for a category and inserts the
        final deviation value to ensure total deviation is 0, i.e. demand that
        
        SumOverCategory(category_deviation * number_of_films_in_category) = 0
        
        Parameters
        ----------
        
        devArray: array like
            the log_10 deviation from the average runtime for films by category
            (country, language and genre) for both writer-director overlap and
            non-overlap. The list should contain the deviations for all but one
            entry in each category.
        
        categoryDict: dictionary
            a dictionary of two elements: "same" and "diff". 
            categoryDict['same'] and categoryDict['diff'] each contain an array 
            of two element lists. Each pair is the name of an entry in the 
            category (e.g. if the cateogry is "genre" then an entry might be 
            "romance") and the number of times that entry appears in the 
            dataframe of all films for overlapping and non-overlapping 
            writer/director respectively. The array is ordered by the number of 
            appearances from smallest to largest.
        
        offset: integer
            the first position in devArray at which entries start corresponding
            to entries in categoryDict
        
        returns
        -------
        
        array like
            as devArray but with an additional value inserted which is the
            predicted deviation for the last entry in categoryDict['diff'] such
            that the weighted sum of all the deviations is 0.
        
        '''
    #get the number of entries for both overlap and non-overlap
    sameLen = categoryDict['same'].shape[0]
    diffLen = categoryDict['diff'].shape[0]

    #calculate the weighted average of entries with writer-director overlap
    CatSameDevTot = sum( np.float64(categoryDict['same'][:,1]) * \
                        devArray[offset:offset+sameLen])
    #calculate the weighted average of entries with non-overlap, excluding final
    #the entry
    CatDiffDevTot = sum( np.float64(categoryDict['diff'][:,1][:-1]) * \
                        devArray[offset+sameLen:offset+sameLen+diffLen-1])
    #determine the final entry
    CatFinalDevVal = (-1.)*(CatSameDevTot + CatDiffDevTot) / \
                                    np.float64(categoryDict['diff'][:,1][-1])
    return np.insert(devArray, offset+sameLen+diffLen-1, CatFinalDevVal)


def get_deviations(same_list, diff_list, deviations, prefix, df, offset):
    '''FOR USE IN FILM_MODEL_BY_YEAR
        calculates the deviations in the runtime from the average for each film
        in df for a particular category
        
        Parameters
        ----------
        
        same_list: array_like of integrers
            number of films in each entry of the category for which the writer 
            was also the director
        
        diff_list: array_like of integrers
            number of films in each entry of the category for which the writer 
            was NOT the director
        
        deviations: array_like
            a list ofthe deviations from the the average runtime for each entry 
            in each category
        
        prefix: string
            entries for a particular category are represented in the dataframe 
            df by the name prefix + entry_name, e.g. when the category is 
            countries, the prefix is "Cou_", for languages it is "Lan_" and for 
            genres it is "Gen_".
        
        df: pandas dataframe
            a dataframe containing the log_10 runtime of films, and descriptors 
            denotings the country(ies) the film was made in, the language(s) 
            spoken in it and the genre(s) that descibe it.
        
        offset: integer
            the first position in deviations at which entries correspond to the 
            chosen category
        
        Returns
        -------
        
        tuple of array_likes
            the first array is the deviations from the average associated with
            the chosen category when the writer is also the director. The second
            is for deviations when the writer is NOT the director. Note that
            when there is a non-zero value in one array, there will be a
            corresponding zero value in the other array.
        
        '''

    tmp = np.zeros(len(df))
    same = pd.Series(tmp)
    diff = pd.Series(tmp)
    len_same_list=len(same_list)
    #for each film add all the deviations corresponding to each category
    for i, deviation in enumerate(same_list):
    same=same.add(deviations[i + offset]*df[prefix+deviation].values)
    for i, deviation in enumerate(diff_list):
    diff = diff.add(deviations[i + len_same_list + offset] * \
                    df[prefix+deviation].values)
    #divide by the number of different category entries
    same /= df[prefix+'TOTAL'].values
    diff /= df[prefix+'TOTAL'].values
    return df[u'Overlap'].values*same, df[u'nonOverlap'].values * diff



