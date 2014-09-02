#!/usr/bin/env python
# encoding: utf-8
# Daniele Trifirò
# brethil@phy.olemiss.edu
# 11 July 2014
#
#
# Takes as arguments a file with a list with tab separated GPS times
# and a PCAT configuration file and runs PCAT on the given GPS times/config
#
# Usage:
#   PCAT_configread.py GPS_list config_file_time [conf_file_freq]
#
# If the frequency configuration file is omitted only the time_domain analysis 
# is run.
#
#



import sys
import os
import shutil
import subprocess


import numpy as np
import PCAT

from string import join


IMAGE_WIDTH = 1500
DPI = 80
IMAGE_HEIGHT = 2*DPI

import optparse
from gwpy.segments import (DataQualityFlag, DataQualityDict)

def parse_commandline():
    """
    Parse the options given on the command-line.
    """
    parser = optparse.OptionParser()
    default_time_config = "/home/brethil/cron_PCAT/PCAT_cron-time.config"
    default_frequency_config = "" #"/home/brethil/cron_PCAT/PCAT_cron-frequency.config"
    #TODO: ADD A WARNING IF FILE DOES NOT EXIST AND FALLBACK TO THE DEFAULT
    parser.add_option("-l", "--list", help="List file containing tab separated GPS times",default=None)
    parser.add_option("-s", "--start", help="GPS time start",default=None)
    parser.add_option("-e","--end", help="GPS time end", default=None)
    parser.add_option("-t", "--time", help="Time Domain configuration file, optional, defaults to " + default_time_config, default=default_time_config)
    parser.add_option("-f", "--frequency", help="Frequency Domain configuration file, optional, defaults to " + default_frequency_config, default=default_frequency_config)
    parser.add_option("-n", "--name", help="Name for output file (if using -s and -e)", default=None)
    opts, args = parser.parse_args()

    return opts

def read_config_time(file_name):
    f = open(file_name, "r")
    channel_list = f.read().split("\n")
    f.close()
    configurations = []
    for line in channel_list:
        if ( line != '' ) and ("#" not in line):
            configurations.append(line.split())
    assert (len(configurations) > 0), "Configuration file is empty!" 
    
    channel_names = []
    IFOs = []
    frame_types = []
    thresholds = []
    variables_number = []
    highpass_cutoff = []
    whitening = []
    downsample_freq = []
    segment_size = []
    components_number = []
    max_clusters = []
    for configuration in configurations:
        channel_names.append(configuration[0])
        IFOs.append(configuration[1])
        frame_types.append(configuration[2])
        thresholds.append(configuration[3])
        variables_number.append(configuration[4])
        highpass_cutoff.append(configuration[5])
        whitening.append(configuration[6])
        downsample_freq.append(configuration[7])
        segment_size.append(configuration[8])
        components_number.append(configuration[9])
        max_clusters.append(configuration[10])
        
    configuration = (channel_names, IFOs, frame_types, thresholds, variables_number, highpass_cutoff, whitening, downsample_freq, segment_size, components_number, max_clusters)
    
    return configuration

def read_config_frequency(file_name):
    f = open(file_name, "r")
    channel_list = f.read().split("\n")
    f.close()
    configurations = []
    for line in channel_list:
        if ( line != '' ) and ("#" not in line):
            configurations.append(line.split())
    assert (len(configurations) > 0), "Configuration file is empty!" 
    
    channel_names = []
    IFOs = []
    frame_types = []
    thresholds = []
    variables_number = []
    highpass_cutoff = []
    whitening = []
    downsample_freq = []
    segment_size = []
    components_number = []
    max_clusters = []
    for configuration in configurations:
        channel_names.append(configuration[0])
        IFOs.append(configuration[1])
        frame_types.append(configuration[2])
        variables_number.append(configuration[3])
        segment_size.append(configuration[4])
        components_number.append(configuration[5])
        max_clusters.append(configuration[6])
        
    configuration = (channel_names, IFOs, frame_types, variables_number, segment_size, components_number, max_clusters)
    
    return configuration
    

def run_PCAT_time(list_name, configuration, start_time, end_time):
    global opts, channel_processing_errors
    (channel_names, IFOs, frame_types, thresholds, variables_number, highpass_cutoff, whitening, downsample_freq, segment_size, components_number, max_clusters) = configuration
    args = []
    results = []
    for index in range(len(channel_names)):
        # Example of typical args:
        # "PCAT.py --time --whiten --highpasscutoff 10 -t 4.0 --IFO L --frame
        #   L1_R -c L1:LSC-DARM_IN1_DQ --list summary_24-July-2014
        #   --reconstruct --components 10 -m 6"
        
        if opts.start and opts.end:
            arg = "PCAT.py --silent --time {0} --channel {1} --IFO {2} --frame {3} --list {4} --size {5} --highpasscutoff {6} -t {7} -v {8} --components {9} -m {10} --resample {11} --reconstruct --glitchgram_start {12} --glitchgram_end {13}".format('--whiten' if (whitening[index] == "YES") else '', channel_names[index], IFOs[index], frame_types[index], list_name, segment_size[index], highpass_cutoff[index], thresholds[index], variables_number[index], components_number[index], max_clusters[index], downsample_freq[index], start_time, end_time)
        else:
            arg = "PCAT.py --silent --time {0} --channel {1} --IFO {2} --frame {3} --list {4} --size {5} --highpasscutoff {6} -t {7} -v {8} --components {9} -m {10} --resample {11} --reconstruct".format('--whiten' if (whitening[index] == "YES") else '', channel_names[index], IFOs[index], frame_types[index], list_name, segment_size[index], highpass_cutoff[index], thresholds[index], variables_number[index], components_number[index], max_clusters[index], downsample_freq[index])
        args.append(arg.split())
    for index, configuration in enumerate(args):
        print "Processing {0}...".format(channel_names[index])
        try:
            URL = PCAT.pipeline(configuration)
        except:
            import traceback
            error = traceback.format_exc()
            join(error.split("\n"), "</br>")
            print "Exception: {0}".format(error)
            channel_processing_errors += "- Time Domain: error processing channel: {0}, error:</br>".format(channel_names[index])
            channel_processing_errors += "\t{0}</br>".format(error)
            URL = "PROCESSINGERROR"
        results.append((channel_names[index], URL))

    
    return results
    
def run_PCAT_frequency(list_name, configuration):
    global channel_processing_errors
    (channel_names, IFOs, frame_types, variables_number, segment_size, components_number, max_clusters) = configuration
    args = []
    results = []
    for index in range(len(channel_names)):
        # Example of typical args:
        # PCAT.py --frequency --size 10 --IFO L --frame L1_R
        # -c L1:LSC-DARM_OUT_DQ --start 1090221815 --end 1090222285
        # --list list_name -m 10 --components 40 -v 8192
        
        arg = "PCAT.py --silent --frequency --channel {0} --IFO {1} --frame {2} --list {3} --size {4} -v {5} --components {6} -m {7} --reconstruct".format(channel_names[index], IFOs[index], frame_types[index], list_name, segment_size[index], variables_number[index], components_number[index], max_clusters[index])
        args.append(arg.split())
    for index, configuration in enumerate(args):
        print "Processing {0}...".format(channel_names[index])
        try:
            URL = PCAT.pipeline(configuration)
        except:
            import traceback
            error = traceback.format_exc()
            join(error.split("\n"), "</br>")
            print "Exception: {0}".format(error)
            channel_processing_errors += "- Frequency Domain: error processing channel: {0}, error:</br>".format(channel_names[index])
            channel_processing_errors += "\t{0}</br>".format(error)
            URL = "PROCESSINGERROR"
        results.append((channel_names[index], URL))
    
    return results

def print_html_table(list_path, output_dir, results_time, results_frequency=None):
    global channel_processing_errors
    try:
        os.makedirs( output_dir )
    except:
        pass
    try:
        os.makedirs( output_dir + "/img")    
    except:
        pass
    try:
        os.makedirs( output_dir + "/misc")    
    except:
        pass
    list_name = os.path.basename(list_path)
    output_file = open(output_dir + "/" + list_name + ".html", "w")
    
    print >>output_file, """<html>
    <head>
        <title>Summary - {0}</title>
        <link rel="stylesheet" type="text/css" href="../../style/main.css">
    </head>
    <body>
    <span><table style="text-align: left; width: 1100; height: 100   px; margin-left:auto; margin-right: auto;" border="1" cellpadding="1" cellspacing="1">
        <tbody>
        <tr>
        <td style="text-align: center; vertical-align: top; background-color:SpringGreen;"><big><big><big><big><span style="font-weight: bold;">Summary Page - {0}</span></big></big></big></big>
        </td>
        </tr>
        </tbody>
        </table>
        
        <br>
        <div align="center">  
                <a href='{3}Analyzed_interval.txt'><img src="./img/lock-plot_{0}.png" alt="{0} Locked Plot" width="{1}" height="{2}" align="middle"></a>
            </div>
            
        <br>
        <br>
    <table border="1" style="text-align: left; width: 1200; height: 67px; margin-left:auto; margin-right: auto; background-color: white;" b\
order="1" cellpadding="2" cellspacing="2" align=center><col width=250> <col width=120><col width=120><col width=170> <col width=120><col width=200>""".format(list_name, int(IMAGE_WIDTH*0.75), int(IMAGE_HEIGHT*0.75), results_time[0][1])
    
    if (results_frequency):
        # Print table headers including frequency domain
        print >>output_file, "<tr><th>Channel name</th><th align='right'>Time Domain</th><th align='right'>Glitchgram</th><th align='right'>Time Domain parameters</th><th align='right'>Frequency Domain</th><th align='right'>Frequency Domain parameters</th></tr>"
        for index, results in enumerate(results_time):
            if (results[1]):
                print >>output_file, "<tr><td>{0}</td><td align='right'><a href='{1}'>Results</a></td><td align='right'><a href='{1}Glitchgram.html'>glitchgram</a></td><td align='right'><a href='{1}parameters.txt'>parameters</a></td><td align='right'><a href='{2}'>Results</a></td><td align='right'><a href='{2}parameters.txt'>parameters</a></td></tr>".format(results[0], results[1], results_frequency[index][1])
            else:
                print >>output_file, "<tr><td>{0}</td><td align='right'>No glitches found</td><td align='right'> </td></td> <td align='right'><a href='{1}'>Results</a> (<a href='{1}parameters.txt'>parameters</a>)</td></tr>".format(results[0], results_frequency[index][1])    
    else:
        # Print only time domain headers
        print >>output_file, "<tr><th>Channel name</td><th align='right'>Time Domain</th> <th align='right'>Glichgram</th><th align='right'>Time Domain parameters</th></tr>"
        for index, results in enumerate(results_time):
            if (results[1]):
                print >>output_file, "<tr><td>{0}</td><td align='right'><a href='{1}'>Results</a><td align='right'><a href='{1}Glitchgram.html'>glitchgram</a></td><td align='right'><a href='{1}parameters.txt'>parameters</a></td></tr>".format(*results)    
            else:
                print >>output_file, "<tr><td>{0}</td><td align='right'>No glitches found</td><td align='right'> </td> <td align='right'> </td></tr>".format(results[0])
    
    if (results_frequency):
        configstring = """Configuration files: <a href="./misc/config_{0}_time.txt">time</a>, <a href="./misc/config_{0}_frequency.txt">frequency</a>""".format(list_name)
    else:
        configstring = """<a href="./misc/config_{0}_time.txt">Configuration file</a>""".format(list_name)
    
    global original_command
    original_command_string = join(original_command, " ")
    
    if channel_processing_errors == "":
        error_list = ""
    else:
        error_list = "<b>Errors:</b> </br>" + channel_processing_errors
    
    print >>output_file, """</table></span> {0}
    <div align="bottom"><p>{1}</p>
    </div>
    </br>
    </br>
    <p> Original command: </br>
    {2}
    </p>
    {3}
    </body></html>""".format("</br>"*(len(results_time)+5), configstring, original_command, error_list)
    
    output_file.close()


def locked_times_plot(list_path, out_path, start_time, end_time):
    """
        list_path: containing path to list file to use (tab or space separated GPS times)
        out_path: path where to write output plot
        start_time: GPS time where the lock plot should start
        end_time: GPS time where the lock plot should end
    """
    import matplotlib
    import matplotlib.pyplot as plt
    import numpy as np
    f = open(list_path, "r")
    times = []
    tmp = f.read().split("\n")
    
    # This if is used to make an empty plot when no locked times are found
    if ("No segments available for GPS " in tmp[0]):
        print "No segments available, print red only plot"
        times = []
    else:
        for element in tmp:
            # Only proceed if line is not empty
            if (element.strip()):
                tmp1 = element.split()
                # We have just read strings, convert to integers:
                times.append( [int(tmp1[0]), int(tmp1[1])] )
    

    
    fig = plt.figure(figsize=(int(IMAGE_WIDTH/DPI),int(IMAGE_HEIGHT/DPI)), dpi=DPI)
    ax = fig.add_subplot(111, axisbg="red", alpha=0.3)
    
    ax.set_xlabel("Time [GPS time]")
    
    x_axis = []
    for segment in times:
        x_axis += np.arange(segment[0], segment[1]+1).tolist()
    
    # Define ticks
    x_ticks = []
    x_ticks_labels = []
    interval = end_time-start_time
    #step = int(np.round((interval)//((IMAGE_WIDTH/DPI)-1)/100.0))*100
    step = (interval)//((IMAGE_WIDTH/DPI)-1)
    
    for t in range(start_time, end_time, step):
        x_ticks.append(t)
        x_ticks_labels.append(str(t))
        
    plt.xticks(x_ticks, x_ticks_labels, rotation=-15, fontsize=10)
    
    # Plot a list of zeros across all x axis (to have something plotted)
    ax.plot(x_axis, np.zeros(len(x_axis)))
    
    # Make y axis invisible
    #ax.axes.get_yaxis().set_visible(False)
    ax.set_xlim((start_time, end_time))
    ax.set_ylim((0,1))
    # If yticks aren't set to something then the image is not plotted (weird)
    plt.yticks([0,0.7,1],["something","something","dark side"])
    for tick in ax.yaxis.get_major_ticks():
        tick.set_visible(False)
    plt.subplots_adjust(bottom=0.5)
    
    # Uncomment following for Dashed vertical lines
    #ax.xaxis.grid(color="gray", ls="--",alpha=0.3)
    
    # Color in green 
    # the part of the plot corresponding to locked times
    # (defined in the 'times' variable)
    
    #locked_times_plots = []
    
    for interval in times:
        """tmp = np.array(x_axis, dtype="float")
        where = (tmp>=interval[0]) & (tmp<=interval[1])
        locked_times_plots.append(matplotlib.collections.BrokenBarHCollection.span_where(tmp, ymin=0, ymax=1, where=where, facecolor='green', alpha=0.9))
        ax.add_collection(locked_times_plots[-1])"""
        ax.fill([interval[0], interval[1], interval[1], interval[0]], [0,0,1,1], "green")
    
    
    fig.savefig(out_path + "lock-plot_{0}.png".format(os.path.basename(list_path)), bbox_inches='tight', pad_inches=0.01)
    plt.close()

def main():
    argn = len(sys.argv[1:])
    global opts
    opts = parse_commandline()
    
    global original_command, channel_processing_errors
    original_command = join(sys.argv, " ")
    channel_processing_errors = ""
    user_name = os.path.expanduser("~").split("/")[-1]
    output_dir = os.path.expanduser("/home/"+user_name+"/public_html/PCAT_cron")
    
    # Call grid-proxy-init to initialize the robot cert
    subprocess.call(["grid-proxy-init"])
    
    try:
        os.makedirs(output_dir)
    except:
        pass
    
    if (not opts.list) and (not ( opts.start and opts.end)):
        print "Either a list of times or start and end GPS times have to be supplied."
        print "Re-run with -h for usage."
        exit()
    
    # Set an output name if name has not been provided
    if opts.start and not opts.name:
        out_name = str(opts.start)+"-"+str(opts.end)
    
    if opts.start:
        out_name = opts.name
    else:
        out_name = os.path.basename(opts.list)
    
    out_file = out_name
    
    if (opts.start and opts.end):
         start_time = int(opts.start)
         end_time = int(opts.end)
    elif opts.list:
        f = open(opts.list, "r")
        tmp = np.loadtxt(f)
        start_time = int(np.min(tmp))
        end_time = int(np.max(tmp))
        f.close()
        del tmp
    
    if not opts.list:
        if (start_time < 1091836816):
            FLAG_1 = "L1:DMT-XARM_LOCK:1"
            FLAG_2 = "L1:DMT-YARM_LOCK:1"
            FLAG_3 = "L1:DMT-PRC_LOCK:1"
            # Get locked segments for each the three above flags:
            print "Retrieving locked segments..."
            locked = DataQualityDict.query([FLAG_1, FLAG_2, FLAG_3], start_time, end_time, url="https://segdb-er.ligo.caltech.edu")
            locked_times = locked[FLAG_1].active & locked[FLAG_2].active & locked[FLAG_3].active
        else:
            FLAG = "L1:DMT-DC_READOUT_LOCKED:1"
            
            locked_times = DataQualityFlag.query(FLAG, start_time, end_time, url="https://segdb-er.ligo.caltech.edu").active
        # Saved the locked_times list to a txt file in ~/PCAT/out_file 
        times_list = "/home/"+ user_name + "/PCAT/" + out_file
        f = open(times_list, "w")
        if (len(locked_times) > 0):
            for segment in locked_times:
                f.write(str(int(segment[0]))+"\t"+str(int(segment[1]))+"\n")
            f.close()
        else:
            f.write("No segments available for GPS {0} to {1}\n".format(start_time, end_time))
            f.close()
            locked_times_plot(times_list, output_dir + "/img/", start_time, end_time)
            from write_summaries_index import main as final_touch
            final_touch()
            print "Updated summary index."
            
            sys.exit()
    else:
        times_list = opts.list
        out_name = opts.list
        
    
    configuration_file_time = os.path.abspath(opts.time)
    shutil.copyfile(configuration_file_time, output_dir + "/misc/config_" + os.path.basename(times_list) + "_time.txt")
    configuration_time = read_config_time(configuration_file_time)
    if (opts.frequency):
        configuration_file_frequency = os.path.abspath(opts.frequency)
        frequency_configuration = read_config_frequency(configuration_file_frequency)
        shutil.copyfile(configuration_file_frequency, output_dir + "/misc/config_" + os.path.basename(times_list) + "_frequency.txt")
        
    
    # Run time domain analysis
    time_results = run_PCAT_time(times_list, configuration_time, start_time, end_time)
    
    # Also do frequency domain if requested, then print results
    if (opts.frequency):
        frequency_results = run_PCAT_frequency(times_list, frequency_configuration)
        print_html_table(times_list, output_dir, time_results, results_frequency=frequency_results)
    else:
        print_html_table(times_list, output_dir, time_results)
    
    # Write lock_plot
    locked_times_plot(times_list, output_dir + "/img/", start_time, end_time)
    
    # Get server name, username and then print summary page URL
    server = PCAT.__get_server_url__()
    
    print "-"*40
    summary_URL = "{0}~{1}/PCAT_cron/{2}.html\n".format(server, user_name, os.path.basename(times_list))
    print "Done! Summary at:\n{0}".format(summary_URL)
    
    from write_summaries_index import main as final_touch
    final_touch()
    print "Updated summary index."
    
if __name__ == '__main__':
    main()