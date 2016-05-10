Film Runtimes
=============

In this project I aimed to see whether films were shorter when the scriptwriter was also the director. I conjectured that writers who were thinking visually would make shorter movies. To address this question, a list of nearly 200,000 films was collated and then machine learning (specifically a Markov Chain Monte Carlo analysis) was performed.

A complete write-up of this project is contained in film.pdf, it contains more on the motivation behind this project, details on the analysis and a discussion of the results.

Below is a brief description of each of the files contained in this repository. My CV is also included, it contains my email address should you wish to contact me about this project.

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