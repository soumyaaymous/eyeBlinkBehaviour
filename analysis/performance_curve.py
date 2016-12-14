"""performance_curve.py: 

"""
    
__author__           = "Dilawar Singh"
__copyright__        = "Copyright 2016, Dilawar Singh"
__credits__          = ["NCBS Bangalore"]
__license__          = "GNU GPL"
__version__          = "1.0.0"
__maintainer__       = "Dilawar Singh"
__email__            = "dilawars@ncbs.res.in"
__status__           = "Development"

import sys
import os
import matplotlib 
matplotlib.use( 'TkAgg' )
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict
import re

pat = r'MouseS(?P<name>\d+)_SessionType(?P<st>\d+)_Session(?P<sn>\d+)'
mousePat = re.compile( pat )

mice_ = defaultdict( list )

def get_dir_info( path ):
    m = mousePat.search( path )
    if not m:
        return None
    return m.group('name'), m.group('sn'), m.group( 'st' )

def analyze_mouse( mouse_name,  data, datadir ):
    print( '[INFO] Analyzing mouse %s' % mouse_name )
    print( '\t Has %d session' % len(data ) )
    data = sorted( data )
    reference = data[0]
    plt.figure( )
    plt.boxplot( [ x[2] for x in data ] )
    plt.xlabel( 'Sessions' )
    plt.ylabel( 'Area under the curve' )
    plt.title( 'Mouse-%s performance' % mouse_name )
    outfile = os.path.join( datadir, 'performance_mouse_%s.png' % mouse_name )
    plt.savefig( outfile )
    plt.close( )
    print( '[INFO] Saved performance of mouse %s to %s' % (mouse_name, outfile ) )

def main( datadir ):
    global mice_
    for d, sd, fs in os.walk( datadir ):
        info = get_dir_info( d )
        if info is None:
            continue

        try:
            data = np.loadtxt( os.path.join(d, 'area_under_curve.csv') )
            mice_[ info[0] ].append( (int(info[1]), int(info[2]), data ) )
        except Exception as e:
            print( '[WARN] %s has not area_under_curve.csv file' % d )

    # Sort according to session numbers
    for m in mice_:
        analyze_mouse( m, mice_[m], datadir )


if __name__ == '__main__':
    datadir = sys.argv[1]
    main( datadir )
