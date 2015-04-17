# Zebrafish
Contains code for analyzing zebrafish tracking data output from using 
Ctrax (http://ctrax.sourceforge.net/):
Branson et al, High-throughput ethomics in large groups of Drosophila 
(2009). Nature Methods, (6) 451-457.

Analyzes resulting CSV files for time fish spends in top/bottom half of tank, top/middle/bottom third of tank, for freezing/immobility, and distance from bottom of the tank.

##Assumptions
Assumes you only have one fish to track. If Ctrax has multiple tracks for the fish, the script will take the latest (most recent) track. This sometimes occurs when the fish moves too quickly and Ctrax interprets it as a new fish.

##Requirements
Python 2.7

In the directory where you run the script you'll need:

1) The CSV output from Ctrax 

2) The .ann file (assumed to be of the default form: filename.movie_extension.ann). The ROI must be defined in the .ann file for the script to work. It pulls out the coordinates of the ROI to use for analysis of where the fish is in the tank.

##Parameters 
Now altered to match syntax of Ctrax; can be done in any order.

--Input= Input file name

--Output= Output file name

--Time= OR fps= length of time of video or FPS for video (if known)

--x= OR --y= maximum x/y distance in ROI defined in .ann file. Allows calibration for distance from bottom of tank (and eventually for other measures); Note this optional, if it is not included the distances will be given in "arbitrary" pixel units.


