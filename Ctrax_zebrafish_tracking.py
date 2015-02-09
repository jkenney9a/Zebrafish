# -*- coding: utf-8 -*-
"""
Code for analyzing zebrafish tracking csv output from Ctrax 

Inputs: 
Argument 1: File of the list of filenames to be analyzed (no extensions)
            or a single csv file output from Ctrax.
Argument 2: Filename of output CSV file
Argument 3: Mode and length (e.g., time=10 or fps=30). 
            Note: time is in minutes, fps = frames per second of video

Output:
CSV file listing the percent time fish spends in different parts of tank divided
by halves and by thirds.

Author: 
Justin W. Kenney
jkenney9a@gmail.com

"""

import pandas as pd
import pickle #To unpickle the coordinates out of the .ann file
import numpy as np
import glob #For use of wild cards in getting .ann files

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

    Output: dataframe of x and y coordinates of fish. Assumes one fish and
    combines different IDs from ctrax into one track.
    """
    
    coordinates = {'x':[], 'y':[]}
    
    for frame in df.index:
        
        #Get x,y coordinates of all ids present in file. The CSV output files
        #from Ctrax are setup in blocks of 6 columns where the 1st is the ID
        # and the 2nd and 3rd or the x and y coordinates, respectively.        
        tracker_ids = range(0,len(df.columns),6)
        x_temp = []
        y_temp = []
        
        for ids in tracker_ids:
            #Ids without tracking info are "-1" in the CSV file under ID
            if df[ids][frame] >= 0:
                x_temp.append(df[ids + 1][frame])
                y_temp.append(df[ids + 2][frame])
        
        #Take the last of the appended coordinates (i.e, last id) and throw out
        #any spurious detections (i.e., len > 0)
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
    top, bottom = coordinates for top and bottom of tank (in same space as tracking data) 
    trial = the time or fps (frames per second), e.g., 5 or 30
    mode = "time" or "fps"
    
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
            #Stop trial at last index;
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
    
    Output: Top, bottom, left, right coordinates for tank as dict
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
   
    #Get largest and smallest x and y coordinates (left/right/top/bottom of tank)
    output = {}
    output["top"] = max([roi[0][i][1] for i in range(len(roi[0]))])
    output["bottom"] = min([roi[0][i][1] for i in range(len(roi[0]))])
    output["left"] = min([roi[0][i][0] for i in range(len(roi[0]))])
    output["right"] = max([roi[0][i][0] for i in range(len(roi[0]))])
        
    return output
    
    

def analyze_file(files, file_type, output, mode):
    """
    Analyzes files
    
    Input: list of filenames, file_type = .txt or .csv, output file name,
    mode ("time=xx" or "fps=xx"), 
    
    Output: None, writes data to the output file
    """
    if file_type == ".txt":
        f = open(sys.argv[1])
        files = [filename.strip('\n') for filename in f]
        files = [filename.strip('.csv') for filename in files]
        f.close()
    
    output_file = open(output,'a')
    
    mode_type = mode[:mode.find('=')].lower()
    
    if mode_type == "time":
    
        trial_length = int(mode[mode.find('=')+1:])
        
        #Add blank lines to output CSV to make it look pretty
        blanks = trial_length * " "
        blank_line = pd.DataFrame(blanks, index = [1], columns = range(trial_length))
        
        if file_type == ".txt":
            for filename in files:
                df = load_data(filename + ".csv")
                df = combine_df(df)
                #glob.glob returns a list; just need element of list.
                #This allows for the use of other types of movies besides .avi
                t_b = get_top_and_bottom(glob.glob(filename + ".*.ann")[0])
                df_out = min_by_min_top_bottom_analysis(df, t_b['top'], t_b['bottom'], 
                                                        trial_length)
                df_out.to_csv(output_file, index_label=filename)
                blank_line.to_csv(output_file, index=False, header=False)
                print filename + " is done!"
        
        elif file_type == '.csv':
            df = load_data(files)
            df = combine_df(df)
            ann_file = glob.glob(files.strip('.csv') + '.*.ann')[0] 
            t_b = get_top_and_bottom(ann_file)
            df_out = min_by_min_top_bottom_analysis(df, t_b['top'], t_b['bottom'], 
                                                        trial_length)
            df_out.to_csv(output_file, index_label=files)
            blank_line.to_csv(output_file, index=False, header=False)
            print files + " is done!"
            
    
    elif mode_type == "fps":
        
        if file_type == ".txt":
            for filename in files:
                df = load_data(filename + ".csv")
                df = combine_df(df)
                fps = float(mode[mode.find('=')+1:])
                fpm = fps*60 #Calculate frames per minute
                trial_length = len(df.index)/float(fpm)
                
                #Add blank lines to output CSV to make it look pretty
                #Need to put it in the loop this time b/c of variable video lengths 
                #using fps mode
                blanks = int(trial_length + 1) * " "
                blank_line = pd.DataFrame(blanks, index = [1], 
                                          columns = range(int(trial_length)))
                
                t_b = get_top_and_bottom(glob.glob(filename + ".*.ann"))[0]
                
                df_out = min_by_min_top_bottom_analysis(df, t_b['top'], t_b['bottom'],
                                                        fps, mode=mode_type)
                df_out.to_csv(output_file, index_label=filename)
                blank_line.to_csv(output_file, index=False, header=False)
                print filename + " is done!"
            
        elif file_type == ".csv":
            df = load_data(files)
            df = combine_df(df)
            fps = float(mode[mode.find('=')+1:])
            fpm = fps*60 #Calculate frames per minute
            trial_length = len(df.index)/float(fpm)
            
            #Add blank lines to output CSV to make it look pretty
            blanks = int(trial_length + 1) * " "
            blank_line = pd.DataFrame(blanks, index = [1], 
                                      columns = range(int(trial_length)))
            
            ann_file = glob.glob(files.strip('.csv') + '.avi.ann')[0]
            t_b = get_top_and_bottom(ann_file)
            
            df_out = min_by_min_top_bottom_analysis(df, t_b['top'], t_b['bottom'],
                                                    fps, mode=mode_type)
            df_out.to_csv(output_file, index_label=files)
            blank_line.to_csv(output_file, index=False, header=False)
            print files + " is done!"
            
            
    output_file.close()
    
if __name__ == "__main__":
    
    import sys
    
    files = sys.argv[1]    
    output = sys.argv[2]
    mode = sys.argv[3]
    
    file_type = files[files.find('.'):].lower()
    
    if file_type == ".txt" or file_type == ".csv":
        analyze_file(files, file_type, output, mode)
    
    else:
        print "Not a supported file type."
        print "File must be a list of filenames in a .txt file or .csv output"
        print "from Ctrax."


    
    
        
