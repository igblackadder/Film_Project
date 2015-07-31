Film Runtimes
=============

An analysis of film runtimes. The purpose of this project is to see if films 
where the scriptwriter went on to be the director were shorter than other movies.
A list of nearly 200,000 movies was collated and then a Bayesian Analysis 
performed to try to answer this question.

Results
-------

The results of the analysis (so far) have been summarized in "Film Runtime 
paper.pdf," this includes the background to the project, a brief description of 
the analysis, and some of the results. The plots from the paper have also been 
included as seperate files in the figures folder. You should download the paper 
as it doesn't always render properly inside github.

Code
----

filmGrab.py defines a class that retrieves a single entry from the Internet 
Movie Database.

filmGather.py contains a script that retrieves the first million entries from 
the Internet Movie Database.

film.Analysis.py defines a model for the distribution runtimes, performs a 
Markov Chain Monte Carlo simulation to find the mean of the runtimes, and then 
plots the results.

Future Work
-----------

There is a lot more work to do on this analysis which I will persue when I have 
the time. The future direction is described at the end of the paper 
("Film Runtime paper.pdf").


