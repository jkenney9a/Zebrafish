# -*- coding: utf-8 -*-
"""
Code for generating tracking/heatmap figures from tracking csv output from Ctrax 

Author: 
Justin W. Kenney
jkenney9a@gmail.com
"""

#import pandas as pd #For working with dataframes
#import pickle #For unpickling objects from .ann files
#import numpy as np
import glob

from ggplot import * #For generating figures

from Ctrax_zebrafish_tracking import *

def path_figure(df, output_name, output_type, top, bottom, left, right,
                boundary=False):
    """
    Input: Cleaned dataframe of tracking data, coordinates for top, bottom, left
    and right of tank/arena containing animal, output file name and file type
    
    Output: Write to file file_name.file_type of the figure
    """
    
    title = output_name.split('.')[0]
    
    if abs(right - left) > (top - bottom):
        lims = [left, right]
    else:
        lims = [bottom, top]
    
    p = ggplot(aes(x='x', y='y'), data=df) +\
    geom_path() +\
    ggtitle(title) +\
    xlab('') + ylab('') +\
    xlim(min(lims), max(lims)) + ylim(min(lims), max(lims)) +\
    theme_bw()
    
    if boundary:
        #Need to work on this to use actual bounds drawn from .ann file for use
        #of non-square boundaries
        bounds = {'x':[left, right, right, left, left], 
                  'y':[bottom, bottom, top, top, bottom]}
        p = p + geom_path(aes(x='x', y='y'), data=bounds)
    
    out_file = output_name.split('.')[0] + '.' + output_type
    
    ggsave(filename=out_file, plot=p, format=output_type)
    
#def heatmap_figure(df, top, bottom, left, right, file_name, file_type='png')

def handle_file(file_name, output_name, out_type, path = False, heat = False,
                boundary=False):
    """
    Input: file_name to be analyzed, the output filename and type, 
    and whether to generate a path and/or heatmap figure 
    
    Output: Figures appropriately saved
    """
    
    #Get data and clean it up (assumes 1 tracked animal)
    df = load_data(file_name)
    df = combine_df(df)
    
    ann_file = glob.glob(file_name.strip('.csv') + '.*.ann')[0] 
    coords = get_top_and_bottom(ann_file)
    
    if path:
        path_figure(df, output_name=output_name, output_type=output_type,
                    top=coords['top'], bottom=coords['bottom'], 
                    left=coords['left'], right=coords['right'], 
                    boundary=boundary)
        

if __name__ == "__main__":
    
    import sys
    
    #Initialize some variables
    path = False
    heat = False
    boundary = False
    
    for arg in sys.argv[1:]:
        try:
            name, value = arg.split('=', 1)
            
        except:
            print "Error parsing command line argument. No '=' found"
        
        if name.lower() == "--input":
            input_file = value
            input_type = input_file.split('.')[1]
        
        elif name.lower() == "--output":
            output = value
            output_type = output.split('.')[-1]
        
        elif name.lower() == "--figure":
            figures = value.split(',')
            figures = [x.lower() for x in figures] #Make things case insensitive
            if 'path' in figures:
                path = True
            elif 'heat' in figures:
                heat = True
        elif name.lower() == "--boundary":
            boundary = value.lower()
            if boundary == 't':
                boundary = True
        
    handle_file(input_file, output, output_type, path=path, heat=heat,
                boundary=boundary)
        
                
            
        
    
    