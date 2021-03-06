"""analyze_trial.py: 

Analyze each trial.

"""
    
__author__           = "Dilawar Singh"
__copyright__        = "Copyright 2016, Dilawar Singh "
__credits__          = ["NCBS Bangalore"]
__license__          = "GNU GPL"
__version__          = "1.0.0"
__maintainer__       = "Dilawar Singh"
__email__            = "dilawars@ncbs.res.in"
__status__           = "Development"

import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatch
import itertools
import random 
import logging
import pandas

try:
    plt.style.use( 'ggplot' )
except Exception as e:
    pass

#plt.rcParams.update({'font.size': 8, 'text.usetex' : True })

columns_ = [ 'time', 'sensor', 'trial_count', 'tone', 'puff', 'led', 'status'
        , 'imaging' ]

aN, bN = 0, 0
toneBeginN, toneEndN = 0, 0
puffBeginN, puffEndN = 0, 0
data = None
tone = None
puff = None
led = None
status = None
cstype = 1              # Always 1 for this branch
trial_type = 'CS_P'     # cs+, distraction, or probe
time = None
newtime = None
sensor = None
trialFile = None
args_ = None


def plot_raw_trace( ax, data ):
    time, sensor = data['time'], data['sensor'] 
    preData = data[ data['status'] == 'PRE_' ]
    postData = data[ data['status'] == 'POST' ]

    toneData = data[ data['status'] == 'TONE' ]
    puffData = data[ data['status'] == 'PUFF' ]

    ax.plot( time, sensor )
    ax.plot( preData['time'], preData['sensor'], label = 'PRE')
    ax.plot( postData['time'], postData['sensor' ], label = 'POST' )

    ttime = toneData['time'].values
    ntones = (ttime[-1] - ttime[0]) / 300
    for i in range( ntones ):
        ax.plot( ttime[0] + 300 * i, sensor.mean() - 300
                , marker=r"$\uparrow$"
                )
    try:
        ptime = puffData['time'].values
        ax.plot( ptime[0],  sensor.mean() - 300, marker='$P$' )
    except Exception as e:
        # No puff here
        pass

    ax.legend( framealpha = 0.4 )
    plt.xlim( (0, max(time)) )
    plt.ylim( (sensor.min()-100, sensor.max() + 200 ) )
    plt.xlabel( 'Time (ms)' )
    plt.ylabel( 'Sensor readout' )

def plot_zoomedin_raw_trace( ax ):
    global time, newtime
    global puff, tone, led
    global puffBeginN, puffEndN
    global toneBeginN, toneEndN
    global aN, bN
    scaleT = 0.1
    time0A = time[:aN] * scaleT 
    timeAB = time[aN:bN] -  time[aN] + time[int(scaleT*aN)]
    timeBX = timeAB[-1] + (time[bN:] - time[bN]) * scaleT
    newtime = np.concatenate( ( time0A, timeAB, timeBX ) )
    plt.plot( newtime[:aN], sensor[:aN] , color = 'b')
    plt.plot( newtime[aN-1:bN], sensor[aN-1:bN], color = 'r')
    plt.plot( newtime[bN:], sensor[bN:] , color = 'b')
    plt.xticks( [0, newtime[aN], newtime[bN], max(newtime) ]
            , [0, time[aN], time[bN], int(max(time)) ] 
            )
    ax.set_xlim(( 0, max(newtime) ))
    ax.set_ylim(( max(0,min(sensor)-200) , max(sensor)+100))
    add_puff_and_tone_labels( ax, newtime)
    plt.xlabel( 'Time (ms)' )
    plt.ylabel( 'Sensor readout' )

def plot_histogram( ax, data):
    """Here we take the data from ROI (between aN and bN). A 100 ms window (size
    = 10) slides over it. At each step, we get min and max of window, store
    these values in a list. 

    We plot histogram of the list
    """
    time, sensor = data['time'], data['sensor']

    preData = data[ data['status'] == 'PRE_' ]
    postData = data[ data['status'] == 'POST' ]

    ax.hist( preData['sensor'].values
            , label = 'PRE'
            , histtype = 'step'
            , bins = 50, lw = 2
            )
    ax.hist( postData['sensor'].values
            , label = 'POST'
            , histtype = 'step'
            ,  bins = 50, lw = 2
            )
    ax.legend( framealpha=0.4)

def determine_trial_type( last_column ):
    assert len( last_column ) > 50, 'Few entries %s' % len( last_column )
    if 'DIST' in last_column:
        return 'DIST'
    elif ('CS_P' in last_column) and ('PUFF' not in last_column ):
        return 'PROB'
    else:
        return 'CS_P'

def parse_csv_file( filename ):
    global trial_type
    print( '[DEBUG] Reading %s' % filename )
    data = pandas.read_table( filename
            , names = columns_
            , sep = ',', comment = '#', skiprows = 5 )
    return "", data

def find_zeros( y ):
    posEdge, negEdge = [], []
    if y[0] < 0:
        negEdge.append( 0 )
    else:
        posEdge.append( 0 )

    for i, x in enumerate(y[1:]):
        # y[i] is previous value if x in current value
        if y[i] >= 0 and x < 0:
            negEdge.append( i )
        elif y[i] <= 0 and x > 0:
            posEdge.append( i )
    return (negEdge, posEdge)

def area_of_signal_per_sec( name, baseline = 0.0 ):
    signal = data[ data['status'] == name ]['sensor'].values
    time = data[ data['status'] == name ]['time'].values
    tdiff = np.diff( time )
    # area using the simple rectangle based approximation
    area = np.sum( tdiff * np.abs( signal - baseline )[1:] ) / 1000.0
    return area


def compute_area_under_curve( data ):
    """
    Compute the baseline which is mean of signal value in PRE_ 
    Substract this value from TONE and TRAC, compute the are under the curve
    after turning negative to posititves.
    """
    preData = data[ data['status'] == 'PRE_' ]['sensor'].values
    assert preData.size > 0
    baseline = np.mean( preData )

    toneArea = area_of_signal_per_sec( 'TONE', baseline )
    traceArea = area_of_signal_per_sec( 'TRAC', baseline )
    return toneArea + traceArea

def main( args ):
    global cstype, trialFile
    global tone, puff, led
    global data, sensor, time
    global status
    global trial_type
    trialFile = args['input']
    plot = args.get('plot', True)
    logging.debug('Processing file %s' % trialFile )
    metadata, data = parse_csv_file( trialFile )
    if len( data ) <= 10:
        logging.debug( 'Few or no entry in this trial' )
        return (None,None)
    if plot:
        plt.figure( )
        ax = plt.subplot(2, 1, 1)
        plot_raw_trace( ax, data )

        ax = plt.subplot(2, 1, 2)
        try:
            plot_histogram( ax, data )
        except Exception as e:
            logging.warn( 'Failed to plot histogram' )
            logging.warn( '\t Error was %s' % e )

        plt.suptitle( os.path.basename(trialFile) )
        outfile = args.get('output', False) or '%s%s.png' % (trialFile, '')
        logging.info('\tPlotting trial to %s' % outfile )
        plt.tight_layout( )
        plt.savefig( outfile )
        plt.close()

    # Compute area under the curve and add that to data 
    aoc = compute_area_under_curve( data )
    return (aoc, data)

if __name__ == '__main__':
    import argparse
    # Argument parser.
    description = '''description'''
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--input', '-i'
        , required = True
        , help = 'Input file'
        )
    parser.add_argument('--output', '-o'
        , required = False
        , help = 'Output file'
        )
    parser.add_argument( '--debug', '-d'
        , required = False
        , default = 0
        , type = int
        , help = 'Enable debug mode. Default 0, debug level'
        )
    class Args: pass 
    args = Args()
    parser.parse_args(namespace=args)
    main( vars(args) )
