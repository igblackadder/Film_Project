Film Runtimes
=============

An analysis of film runtimes. The purpose is to see if films where the scriptwriter went on to be the director were shorter than other movies. It was hypothesized that writers who were thinking visually would make shorter movies. This list of nearly 200,000 movies was collated and then a Bayesian Analysis performed to try to asses this hypothesis.

Files
-----

filmGrab.py defines a class that looks up an entry on imdb and scrapes data such as title and runtime

filmGather.py uses the class in filmGrab.py to get data on a large number of films and write them to the file film_data.txt If there is a problem accessing the page (such as by a server timeout) then that is logged  in the file film_fail.txt

filmWrangle.py wrangles the data for analysis

filmModelMCMC.py defines the model for the data and performs a Markov Chain Monte Carlo analysis to find the values of the model's parameters. These results are written to results.csv

filmPlot.py plots the results of the MCMC and performs a gaussian process regression

film_data.txt is the data on all the movies that were successfully scraped by filmGather.py

film_fail.txt is a log of all the times that the web scraper failed, perhaps due to a server timeout

film_wrangled.csv is the data cleanly presented after wrangling

categories.txt is a list of all the countries, languages and genres present in the data

results.csv are the results of the MCMC and contain the best fit and confidence intervals for the model parameters

plots/ contains the plots of the film runtimes. The file average.pdf shows the overall trend in film runtimes for all movies. Then each country file shows how the films from that country have deviated from that trend. They are presented as a comparison between films in which the writer was also the director and those for which that wasn't the case.

Results
-------

The plot average.pdf shows that film runtimes increased steadily over the first few decades of film history but more recently has started to level off.

The other plots show wide variation accross countries. In the USA films since 1960 have been shorter when the writer was also a director but that was not the case in early cinema. Having the writer also be the director also led to shorter movies in the UK, France, Australia and many other western nations perhaps suggesting a broad cultural trend. However the opposite was found in a number of countries including China.

The Model
---------

Film runtimes were modeled by year. Within each year the distribution of runtimes was assumed to be a gaussian. The mean of the gaussian was the sum of a global trend and deviations from each country involved in the films production. To ensure the deviations really were just deviations, the model demanded that the weighted sum of the deviations equalled zero (weighted by the number of films made in that country).

\\[1_{n}\\]

To Do
-----

The analysis is still being updated and a comprehensive write up of the results is currently being produced.
 

