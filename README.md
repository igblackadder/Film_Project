Film Runtimes
=============

An analysis of film runtimes. The purpose is to see if films are shorter when the script-writer and the director are the same person as it was conjectured that writers who were thinking visually would make shorter movies. A list of nearly 200,000 films was collated and then a Markov Chain Monte Carlo analysis was performed to asses this hypothesis.

A complete write-up of this project is contained in film.pdf, it contains more motivation of the hypothesis, details of the model and a discussion of the results.

Files
-----

film.pdf is a report detailing the hypothesis, the steps taken to get the data and a detailed look at the model used in the analysis. Finally there is a discussion of the results.

filmObtainItem.py defines a class that looks up an entry on imdb.com and scrapes data about a movie such as the title and runtime

filmObtainDataset.py uses the class in filmObtainItem.py to get data on a large number of films and write them to the file film_data.txt. If there is a problem accessing the imdb.com page (such as by a server timeout) then that is logged in the file film_fail.txt

filmWrangle.py cleanes and prepares the data for analysis, producing the file film_wrangled.csv

filmModel.py defines a model for the data, defining a global average and deviations from that average for each country, language and genre.

filmMCMC.py performs a Markov Chain Monte Carlo analysis using the model defined in film.Model.py to find the values of the model's parameters. The results are written to results.csv

filmPlot.py plots the results of the MCMC and performs a gaussian process regression to find the "Slow trend"

film_data.txt is the data on all the movies that were successfully scraped by filmObtainDataset.py

film_fail.txt is a log of all the times that the web scraper failed, perhaps due to a server timeout

film_wrangled.csv is the data cleanly presented after wrangling

categories.txt is a list of all the countries, languages and genres present in the data

results.csv are the results of the MCMC and contain the best fit and confidence intervals for the model parameters

plots/ contains the plots of the film runtimes. The file Global.pdf shows the overall trend in film runtimes for all movies. Then each country file shows how the films from that country have deviated from that trend. They are presented as a comparison between films in which the writer was also the director (labelled "Same")and those where that wasn't the case (labbeled "Different").