# -*- coding: utf-8 -*-
"""
Code for analyzing zebrafish tracking csv output from Ctrax 

Author: 
Justin W. Kenney
jkenney9a@gmail.com

Parameters: 
--Input=<input file name>
--Output=<output file name>
--time= OR fps= the time length of trial or the fps of the video analyzed
--x= OR --y= the maximum x or y length in the .ann ROI

Output:
CSV file listing the percent time fish spends in different parts of tank divided
by halves and by thirds. Also includes time spent freezing (default is 
less than 2 pixels movement over 0.5 seconds) and average distance fish is from
the bottom of the tank at each minute (can be in real or arbitrary distance units).

"""

import pandas as pd #Use dataframes to organize data
import pickle #To unpickle the tank coordinates out of the .ann file
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

def analyze_frame_left_right(df, frame, left, right):
    """
    Input: dataframe of tracking data
    frame to be analyzed
    right and left coordinates of tank
    
    Output: list containing wherein the tank the fish was (right/left)
    """
    
    #Calculate cutoffs for left/right of tank
    half = ((right - left) / 2) + left
    
    if df['x'][frame] <= half:
        return ['left 1/2']
    else:
        return ['right 1/2']


def analyze_frame_top_bottom(df, frame, top, bottom):
    """
    Input: dataframe of tracking data
    frame to be analyzed
    top and bottom coordinates of tank
    
    Output: list containing where in the tank the fish was
    """
    
    #Calculate cutoffs for each part of the tank
    half = ((top - bottom) / 2) + bottom
    two_thirds = (2*(top - bottom) / 3) + bottom
    one_third = ((top - bottom)/ 3) + bottom
    
    if df['y'][frame] >= half and df['y'][frame] >= two_thirds:
        return ['top 1/2', 'top 1/3']
    elif df['y'][frame] >= half and df['y'][frame] < two_thirds:
        return ['top 1/2', 'middle 1/3']
    elif df['y'][frame] < half and df['y'][frame] >= one_third:
        return ['bottom 1/2', 'middle 1/3']
    elif df['y'][frame] < half and df['y'][frame] < one_third:
        return ['bottom 1/2', 'bottom 1/3']

def distance_from_bottom(df, frame, bottom):
    """
    Input: dataframe of tracking data, frame to be analyze, coordinates for the
    bottom of the tank
    
    Output: distance the object is from the bottom-most coordinate of the tank
    """
    
    dist = df['y'][frame] - bottom
    return dist
    
        
def analyze_freezing(df, frame, bin_size, tolerance=2):
    """
    Input: dataframe of tracking data, frame, and bin size and pixel tolerance
    (i.e, difference in pixel movement over bins to be considered not freezing)
    
    Output: True (freezing) or False (not freezing)
    """
    
    if (frame + bin_size) in df.index:
        #Get all x and y-coordinates and their differences
        x_list = df['x'][frame:frame + bin_size]
        x_diffs = sum(abs(np.diff(x_list)))
        y_list = df['y'][frame:frame + bin_size]
        y_diffs = sum(abs(np.diff(y_list)))
        
        #Determine distance moved in both axes:
        distance = np.sqrt(x_diffs**2 + y_diffs**2)
        if distance <= tolerance:
            return True
        else:
            return False
           
    
        
def min_by_min_top_bottom_analysis(df, tank_coordinates, trial, freeze_bin=0.5, 
                                   mode="time", use_real_dist=False, real_len=["x",0]):
    """
    Input: dataframe of tracking data, 
    top, bottom = coordinates for top and bottom of tank (in same space as tracking data) 
    trial = the time or fps (frames per second), e.g., 5 or 30
    bin size for analyzing freezing data (in seconds)    
    mode = "time" or "fps"
    whether to convert to real distances (instead of "pixel" distances)
    the real length to use for calibration as list ([dimension, length])
    
    Output: df of time spent in various parts of tank, % time freezing and 
    average distance from bottom of tank broken down by minute.
    """
    
    Parameters = ['top 1/2', 'bottom 1/2', 'top 1/3', 'middle 1/3', 'bottom 1/3', 
                  'distance from bottom', 'freezing', 'left 1/2', 'right 1/2']    
    
    top = tank_coordinates['top']
    bottom = tank_coordinates['bottom']
    left = tank_coordinates['left']
    right = tank_coordinates['right']
     
    if mode.lower() == "time":
        trial_length = trial
    
        df_out = pd.DataFrame(index = Parameters, 
                              columns = range(1,trial_length + 1), dtype=float)
                              
        frames_per_min = int(len(df.index) / trial_length)
        frames_per_bin = int((frames_per_min/60)*freeze_bin)
        
        #Find frames at each minute boundary    
        frame_index = [x*frames_per_min for x in range(0,trial_length + 1)]
        
        for i in range(0,len(frame_index)-1):    
            #Stop trial at last index;
            frames = range(frame_index[i],frame_index[i+1])        
            
            #Initialize all parameters to zero
            Output = {x: 0 for x in Parameters}
           
            for frame in frames:
                #Find fish top/bottom
                whereabouts = analyze_frame_top_bottom(df, frame, top, bottom)
                for where in whereabouts:
                    Output[where] += 1
                #Find fish left/right
                whereabouts = analyze_frame_left_right(df, frame, left, right)
                for where in whereabouts:
                    Output[where] += 1
                
                if analyze_freezing(df, frame, frames_per_bin):
                    Output['freezing'] += 1
                    
                Output['distance from bottom'] += distance_from_bottom(df, frame, bottom)
            
            for x in Output.keys():
                df_out[i + 1][x] = (Output[x]/ float(len(frames))) * 100
                   
    elif mode.lower() == "fps":
        fps = trial
        fpm = fps*60
        frames_per_bin = int(fps*freeze_bin)
        trial_length = float(len(df.index)) / fpm
        time_intervals = range(1,int(trial_length + 1))
       
        #Add on any partial minute time at end of trial
        time_intervals.append(int(trial_length) + ((trial_length % 1) * 60/100.0))
        df_out = pd.DataFrame(index = Parameters, columns = time_intervals)
        
        #Add 0 to beginning of time intervals to prevent index out of range errors
        time_intervals.insert(0,0)
        
        for t in range(0,len(time_intervals)-1):
            frames = range(time_intervals[t] * int(fpm), int(time_intervals[t+1] * fpm))
            
            #Initialize all parameters to zero
            Output = {x: 0 for x in Parameters}
            
            for frame in frames:
                whereabouts = analyze_frame_top_bottom(df, frame, top, bottom)
                for where in whereabouts:
                    Output[where] += 1
                
                whereabouts = analyze_frame_left_right(df, frame, left, right)
                for where in whereabouts:
                    Output[where] += 1
                
                if analyze_freezing(df, frame, frames_per_bin):
                    Output['freezing'] += 1
                
                Output['distance from bottom'] += distance_from_bottom(df, frame, bottom)
                    
            for x in Output.keys():
                df_out[time_intervals[t+1]][x] = (np.float64(Output[x]) / len(frames)) * 100
    
    #Correct for the fact that distance from bottom is not a percent like other measures
    df_out.ix["distance from bottom"] = df_out.ix["distance from bottom"] / 100

    if use_real_dist:
        if real_len[0].lower() == "x":
            pix_con = float(real_len[1]) / abs(right - left)
            df_out.ix["distance from bottom"] = df_out.ix["distance from bottom"] * pix_con
        
        elif real_len[0].lower() == "y":
            pix_con = float(real_len[1]) / abs(top - bottom)
            df_out.ix["distance from bottom"] = df_out.ix["distance from bottom"] * pix_con
    
     
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

def pixel_to_length(pixel_length, real_length):
    """
    Input: A length in pixels and a corresponding real length
    
    Output: The physical size of a pixel length in the same units as the real length
    """
    
    return (float(real_length)/pixel_length)


def analyze_file(files, file_type, output, mode, use_real_dist, real_len):
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
                ann_file = glob.glob(filename + ".*.ann")[0]              
                t_b = get_top_and_bottom(ann_file)
                df_out = min_by_min_top_bottom_analysis(df, t_b, trial=trial_length, 
                                                        use_real_dist=use_real_dist, 
                                                        real_len=real_len)
                df_out.to_csv(output_file, index_label=filename)
                blank_line.to_csv(output_file, index=False, header=False)
                print filename + " is done!"
        
        elif file_type == '.csv':
            df = load_data(files)
            df = combine_df(df)
            ann_file = glob.glob(files.strip('.csv') + '.*.ann')[0] 
            t_b = get_top_and_bottom(ann_file)
            df_out = min_by_min_top_bottom_analysis(df, t_b, trial=trial_length, 
                                                    use_real_dist=use_real_dist,
                                                    real_len=real_len)
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
                ann_file = glob.glob(filename + ".*.ann")[0]
                t_b = get_top_and_bottom(ann_file)
                
                df_out = min_by_min_top_bottom_analysis(df, t_b, fps, mode=mode_type,
                                                        use_real_dist=use_real_dist, 
                                                        real_len=real_len)
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
            
            ann_file = glob.glob(files.strip('.csv') + '.*.ann')[0]
            t_b = get_top_and_bottom(ann_file)
            
            df_out = min_by_min_top_bottom_analysis(df, t_b, fps, mode=mode_type,
                                                    use_real_dist=use_real_dist, 
                                                    real_len=real_len)
            df_out.to_csv(output_file, index_label=files)
            blank_line.to_csv(output_file, index=False, header=False)
            print files + " is done!"
            
            
    output_file.close()
    
if __name__ == "__main__":
    
    import sys
    
    use_real_dist = False
    real_len = ["x", 0] #Initizliae whether or not to use real distances for calculations
    
    for arg in sys.argv[1:]:
        try:
            name, value = arg.split('=', 1)
            
        except:
            print "Error parsing command line argument. No '=' found"
        
        if name.lower() == "--input":
            files = value
            file_type = files.split('.')[1]
        
        elif name.lower() == "--output":
            output = value
        
        elif name.lower() == "--time" or name.lower() == "--fps":
            mode = name.split("--")[1] + "=" + str(value)
        
        elif name.lower() == "--x" or name.lower() == "--y":
            real_len = [name.split("--")[1], float(value)]
            use_real_dist = True
    
    file_type = files[files.find('.'):].lower()
    
    if file_type.lower() == ".txt" or file_type.lower() == ".csv":
        analyze_file(files, file_type, output, mode, use_real_dist, real_len)
    
    else:
        print "Not a supported file type."
        print "File must be a list of filenames in a .txt file or .csv output"
        print "from Ctrax."


    
    
        
