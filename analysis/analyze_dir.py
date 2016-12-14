#!/usr/bin/env python

"""analyze_dir.py: 

Analyze a given directory. All trials are accumulated and plotted.

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
import sys
import numpy as np
import dateutil
import dateutil.parser
from collections import defaultdict
import logging
import re
import analyze_trial as at
from scipy.interpolate import interp1d

import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.cm as cm
try:
    mpl.style.use( 'ggplot', { 'axes-grid' : False  } )
except Exception as e:
    print( '[INFO] could not set style %s' % e )
    pass
mpl.rcParams['axes.linewidth'] = 0.1
plt.rc('font', family='serif')


args_ = None
data = []
probes = []
probesIdx = []
xmin_, xmax_ = 100000, -100000

# This is the valid trial time.
min_trial_time_ = 17500      # ms

def interpolate( t, d, start, end, step = 5 ):
    # Nearest gives the best fit.
    f = interp1d( t, d, kind='nearest' )
    tnew = np.arange( start, end, step )
    dnew = f(tnew)
    meanErr = abs(np.mean( dnew ) - np.mean( d ))
    stdErr = abs(np.std( dnew ) - np.std( d )) 
    if meanErr > 1.0:
        print( '[Warn] Got error in mean after resampling %f' % meanErr )
    if stdErr > 2.0:
        print( '[WARN] Got error in std  %f' % stdErr )
    return dnew, tnew 

def plot_subplot( ax, data, title, **kwargs ):
    assert len( data ) > 2
    # Dimention mismatch, use histogram2d
    newImg = []
    tmin = data[0][1].min()
    tmax = data[0][1].max()
    for i, (y,t) in enumerate( data ):
        newImg.append( y )
    newImg = np.vstack( newImg )
    im = ax.imshow( newImg, cmap = "jet"
            , interpolation = 'none', aspect='auto' 
            , extent = (tmin, tmax, 0, newImg.shape[0] )
            )
    ax.set_xlabel( kwargs.get('xlabel', 'Time in ms' ) )
    ax.set_ylabel( kwargs.get( 'ylabel', r'\# Trial' ) )
    ax.set_title( title )
    ax.grid( False )                # Grid is set to False
    ax.set_xlim( [ xmin_, xmax_ ] )
    ax.legend( )
    position = plt.gcf().add_axes([ 0.9,0.1,0.02,0.55])
    plt.colorbar( im, cax = position
            , orientation = 'vertical' )

def resample_data( data ):
    global xmin_, xmax_
    newData = [ ]
    tmin = max( [ x['time'].min() for x in data ] )
    if tmin < xmin_: xmin_ = tmin

    tmax = min([ x['time'].max() for x in data ])
    if tmax > xmax_: xmax_ = tmax 

    for x in data:
        t = x['time'].values
        d = x['sensor'].values
        dnew, tnew = interpolate( t, d, tmin, tmax )
        newData.append((dnew, tnew))
    return newData


def make_summary_plot( ax, data ):
    y, tvec = data[0]
    yvecs = [ y ]
    for d, t in data[1:]:
        yvecs.append( d )
    sum = np.sum( yvecs, axis=0) / len( yvecs )
    ax.plot(tvec, sum )
    ax.set_title( 'Summary of CS+ trials' )
    ax.set_xlabel( 'Time in ms' )
    ax.set_ylabel( 'Avg sensor readout' )
    ax.set_xlim( [ xmin_, xmax_ ] )
    ax.legend( framealpha = 0.4 )

def plot_performance( area_under_curve ):
    global args_ 
    aocfile = os.path.join( args_.output_dir, 'area_under_curve.csv' )
    np.savetxt( aocfile, area_under_curve )
    print( '[INFO] Area under the curve is written to %s' % aocfile )
    plt.hist( area_under_curve, bins = 20 )
    plt.title( 'Area under curve (TRACE and TONE) for each trial' )
    plt.savefig( '%s.png' % aocfile)
    print( '[INFO] Histogram is saved to %s.png' % aocfile )

def main(  ):
    global args_
    if not args_.output_dir:
        args_.output_dir = os.path.join(args_.dir, '_plots')
    if not os.path.isdir( args_.output_dir):
        os.makedirs( args_.output_dir )

    files = {}
    print( '[INFO] Searching in %s' % args_.dir )
    for d, sd, fs in os.walk( args_.dir ):
        for f in fs:
            ext = f.split('.')[-1]
            if ext == 'csv':
                filepath = os.path.join(d, f)
                trialIndex = re.search('Trial(?P<index>\d+)\.csv', filepath) 
                if trialIndex:
                    index = int(trialIndex.groupdict()['index'])
                    files[index] = (filepath, f)

    # Sort the trials according to trial number
    fileIdx = sorted( files )
    if len(fileIdx) == 0:
        print('[WARN] No files found' )
        quit()


    areaUnderCurve = []
    for idx  in fileIdx:
        f, fname = files[idx]
        result = None
        aoc, result = at.main( { 'input' : f
            , 'output' : os.path.join(args_.output_dir, fname+'.png') 
            , 'plot' : args_.plot_trials }
            )
        if result is None or result.empty:
            continue

        tVec = result['time']
        if tVec.max()  < min_trial_time_:
            print( '[WARN] Ignoring file %s' % fname )
            continue


        row = result['sensor']
        if len(row) > 100:
            areaUnderCurve.append( aoc )
            r = row
            # NO PUFF trial
            if idx % 10 == 0:
                print( '[INFO] File %s if probe trial' % idx )
                probes.append( result )
            else:
                data.append( result )

    # Align data to puff.
    alignedData = []
    for d in data:
        # Get the index where puff starts.
        # Get the index where last tone was given, use it to align all data.
        lastToneT = d[ d['status'] == 'TONE' ]['time'].iloc[-1]
        d['time'] = d['time'] - lastToneT 
        alignedData.append( d )

    alignedProbs = []
    for d in probes:
        lastToneT = d[ d['status'] == 'TONE' ]['time'].iloc[-1]
        d['time'] = d['time'] - lastToneT 
        alignedProbs.append( d )


    # Plotting starts here. Before going through the following code make sure
    # that xmin_ and xmax_ are properly set.
    ax1 = plt.subplot2grid((7,1), (0,0), rowspan=2)
    ax2 = plt.subplot2grid((7,1), (2,0), rowspan=3)
    ax3 = plt.subplot2grid((7,1), (5,0), rowspan=2)

    # Before plotting anything, align the date. During this we compute the x-axis
    # span to make sure that eveything align well.
    alignedData = resample_data( alignedData )
    alignedProbs = resample_data( alignedProbs )

    make_summary_plot(ax1, alignedData  )


    plot_subplot( ax2, alignedData, 'Conditioned Stimulus'
            , xlabel = 'Time in ms. Last $T_{TONE}=0$'
            )

    print( 'Plotting probes' )
    plot_subplot( ax3, alignedProbs, 'Probes' 
            , xlabel = 'Time in ms. Last $T_{TONE}=0$'
            )

    outfile = '%s/summary.png' % args_.output_dir
    print('[INFO] Saving file to %s' % outfile )
    plt.suptitle( args_.dir.split('/')[-1].replace('_', ', ')
            , x = 0, y = 0.02
            , fontsize = 8
            , horizontalalignment = 'left'
            )

    plt.tight_layout( rect = (0,0,0.9,1) )
    plt.savefig( outfile )
    plt.close()

    plot_performance( areaUnderCurve )


if __name__ == '__main__':
    import argparse
    # Argument parser.
    description = '''Summaries data in one directory'''
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--dir', '-d'
        , required = True
        , help = 'Directory to seach for behaviour data '
        )

    parser.add_argument('--plot-trials', '-pt'
            , required = False
            , default = False
            , action = 'store_true' 
            , help = 'Do you want to plot trials? (default no)'
            )
    parser.add_argument('--max', '-m'
            , required = False
            , default = -1
            , help = 'Max number of trials to be plotted. Default all'
            )
    parser.add_argument('--subplots', '-s'
        , action = 'store_true'
        , help = 'Each trial in subplot.'
        )
    parser.add_argument('--output_dir', '-o'
        , required = False
        , default = ''
        , help = 'Directory to save results.'
        )
    class Args: pass 
    args_ = Args()
    parser.parse_args(namespace=args_)
    main(  )
