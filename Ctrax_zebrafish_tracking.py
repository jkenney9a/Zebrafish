# -*- coding: utf-8 -*-
"""
Code for analyzing zebrafish csv output from Ctrax

Inputs: 
Argument 1: File of the list of filenames to be analyzed (no extensions)
Argument 2: Filename of output list
Argument 3: Mode and length (e.g., time=10 or fps=30)

Author: 
Justin W. Kenney
HFSP Long-term Fellow
The Hospital for Sick Children
Toronto, ON
Canada

jkenney9a@gmail.com

"""

import pandas as pd
import pickle
import sys
import numpy as np

pd.set_option('display.precision',5)

def load_data(filename):
    """
    Input: filename
    
    Output: dataframe (df) object of data
    """    
    return pd.read_csv(filename, header=None)
    

def combine_df(df):
    """
    Input: dataframe of tracking data (from CSV file)

    Output: dataframe of x and y coordinates of mouse
    """
    
    coordinates = {'x':[], 'y':[]}
    
    for frame in df.index:
                
        tracker_ids = range(0,len(df.columns),6)
        x_temp = []
        y_temp = []
        
        for ids in tracker_ids:
            if df[ids][frame] >= 0:
                x_temp.append(df[ids + 1][frame])
                y_temp.append(df[ids + 2][frame])
        
        #Take the last of the appended coordinates (i.e, last id)
        if len(x_temp) > 0:
            coordinates['x'].append(x_temp[-1])
            coordinates['y'].append(y_temp[-1])
        
    return pd.DataFrame(coordinates, columns = ['x','y'])


def time_per_frame(df, trial_length):
    """
    Input: dataframe of Ctrax data and trial length in minutes

    Output: time in ms of each frame
    """
        
    secs = trial_length * 60
    fps = len(df.index) / secs
    
    return 1.0/fps

def min_by_min_top_bottom_analysis(df, top, bottom, trial, mode="time"):
    """
    Input: dataframe of tracking data, 
    pixel coordinates for top and bottom of tank and mode (time or fps)
    
    Output: df of time spent in various parts of tank broken down by minute
    """
    
    Parameters = ['top 1/2', 'bottom 1/2', 'top 1/3', 'middle 1/3', 'bottom 1/3']    
    
    half = ((top - bottom) / 2) + bottom
    two_thirds = (2*(top - bottom) / 3) + bottom
    one_third = ((top - bottom)/ 3) + bottom
    
    if mode.lower() == "time":
        trial_length = trial
    
        df_out = pd.DataFrame(index = Parameters, 
                              columns = range(1,trial_length + 1), dtype=float)
                              
        frames_per_min = int(len(df.index) / trial_length)
        
        #Find frames at each minute boundary    
        frame_index = [x*frames_per_min for x in range(0,trial_length + 1)]
        
        for i in range(0,len(frame_index)-1):    
            #Stop trial at last index; ignores data after specified length
            frames = range(frame_index[i],frame_index[i+1])        
            Output = {x: 0 for x in Parameters}
           
            for frame in frames:
                if df['y'][frame] >= half and df['y'][frame] >= two_thirds:
                    Output['top 1/2'] += 1
                    Output['top 1/3'] += 1
                elif df['y'][frame] >= half and df['y'][frame] < two_thirds:
                    Output['top 1/2'] += 1
                    Output['middle 1/3'] += 1
                elif df['y'][frame] < half and df['y'][frame] >= one_third:
                    Output['bottom 1/2'] += 1
                    Output['middle 1/3'] += 1
                elif df['y'][frame] < half and df['y'][frame] < one_third:
                    Output['bottom 1/2'] += 1
                    Output['bottom 1/3'] += 1
            
            for x in Output.keys():
                df_out[i + 1][x] = (Output[x]/ float(len(frames))) * 100
                   
    elif mode.lower() == "fps":
        fps = trial
        fpm = fps*60
        trial_length = float(len(df.index)) / fpm
        time_intervals = range(1,int(trial_length + 1))
       
        #Add on any partial minute time at end of trial
        time_intervals.append(int(trial_length) + ((trial_length % 1) * 60/100.0))
        df_out = pd.DataFrame(index = Parameters, columns = time_intervals)
        
        #Add 0 to beginning of time intervals to prevent index out of range errors
        time_intervals.insert(0,0)
        
        for t in range(0,len(time_intervals)-1):
            frames = range(time_intervals[t] * int(fpm), int(time_intervals[t+1] * fpm))
            Output = {x: 0 for x in Parameters}
            for frame in frames:
                if df['y'][frame] >= half and df['y'][frame] >= two_thirds:
                    Output['top 1/2'] += 1
                    Output['top 1/3'] += 1
                elif df['y'][frame] >= half and df['y'][frame] < two_thirds:
                    Output['top 1/2'] += 1
                    Output['middle 1/3'] += 1
                elif df['y'][frame] < half and df['y'][frame] >= one_third:
                    Output['bottom 1/2'] += 1
                    Output['middle 1/3'] += 1
                elif df['y'][frame] < half and df['y'][frame] < one_third:
                    Output['bottom 1/2'] += 1
                    Output['bottom 1/3'] += 1
                    
            for x in Output.keys():
                df_out[time_intervals[t+1]][x] = (np.float64(Output[x])/ len(frames)) * 100
    
    return df_out





def get_top_and_bottom(ann_file):
    """
    Input: Annotation file output from Ctrax
    
    Output: Top and bottom coordinates for tank as dict
    """
    #Pulls out the pickled ROI object, which is a numpy array of the coordinates
    with open(ann_file, 'r') as f:
        for line in f:
            if line.find("roipolygons") != -1:
                line2 = str()
                roi_string = str()
                while "hm_cutoff" not in line2:
                    line2 = next(f)
                    roi_string += line2
    
    #Unpickle the sucker
    roi = pickle.loads(roi_string)
   
    #Get largest and smallest y coordinates
    output = {}
    output["top"] = max([roi[0][i][1] for i in range(len(roi[0]))])
    output["bottom"] = min([roi[0][i][1] for i in range(len(roi[0]))])
    output["left"] = min([roi[0][i][0] for i in range(len(roi[0]))])
    output["right"] = max([roi[0][i][0] for i in range(len(roi[0]))])
        
    return output
    

def main():
    f = open(sys.argv[1])
    files = [filename.strip('\n') for filename in f]
    f.close()
    All_output = open(sys.argv[2], 'a')
    
    mode = sys.argv[3]
    
    #Pull out the mode type from the second argument    
    mode_type = mode[:mode.find('=')].lower()
    
    if mode_type == 'time':
    
        trial_length = int(mode[mode.find('=')+1:])
        
        #Add blank lines to output CSV to make it look pretty
        blanks = trial_length * " "
        blank_line = pd.DataFrame(blanks, index = [1], columns = range(trial_length))
        
        for filename in files:
            df = load_data(filename + ".csv")
            df = combine_df(df)
            t_b = get_top_and_bottom(filename + ".avi.ann")
            df_out = min_by_min_top_bottom_analysis(df, t_b['top'], t_b['bottom'], 
                                                    trial_length)
            df_out.to_csv(All_output, index_label=filename)
            blank_line.to_csv(All_output, index=False, header=False)
            print filename + " is done!"
    
    elif mode_type == 'fps':
        
        for filename in files:
            df = load_data(filename + ".csv")
            df = combine_df(df)
            fps = float(mode[mode.find('=')+1:])
            fpm = fps*60
            trial_length = len(df.index)/float(fpm)
            
            #Add blank lines to output CSV to make it look pretty
            #Need to put it in the loop this time b/c of variable video lengths 
            #using fps mode
            blanks = int(trial_length + 1) * " "
            blank_line = pd.DataFrame(blanks, index = [1], 
                                      columns = range(int(trial_length)))
            
            t_b = get_top_and_bottom(filename + ".avi.ann")
            
            df_out = min_by_min_top_bottom_analysis(df, t_b['top'], t_b['bottom'],
                                                    fps, mode=mode_type)
            df_out.to_csv(All_output, index_label=filename)
            blank_line.to_csv(All_output, index=False, header=False)
            print filename + " is done!"
    
    All_output.close()
    
#main()

    
    
        
