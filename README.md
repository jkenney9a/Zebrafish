# Zebrafish
Contains code for analyzing zebrafish tracking data output from using 
Ctrax (http://ctrax.sourceforge.net/):
Branson et al, High-throughput ethomics in large groups of Drosophila 
(2009). Nature Methods, (6) 451-457.

##Assumptions
Assumes you only have one fish to track. If Ctrax has multiple tracks for the fish, the script will take the latest (most recent) track. This sometimes occurs when the fish moves too quickly and Ctrax interprets it as a new fish.

##Requirements
Python 2.7

In the directory where you run the script you'll need:

1) The CSV output from Ctrax 

2) The .ann file (assumed to be of the default form: filename.movie_extension.ann). The ROI must be defined in the .ann file for the script to work. It pulls out the coordinates of the ROI to use for analysis of where the fish is in the tank.

### Example use
At command line type:
python Ctrax_zebrafish_tracking.py input_file output_file time=5

Note: can use either a defined time (in minutes) or defined fps (frames per second) as the third argument.
