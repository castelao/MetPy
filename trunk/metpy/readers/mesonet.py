#!/usr/bin/env python
import numpy as np
from numpy.ma import MaskedArray

#This is a direct copy and paste of the mesonet station data avaiable at
#http://www.mesonet.org/sites/geomeso.csv
#As of November 20th, 2008
mesonet_station_table = '''
  100   2008 08 12  GEOMESO.TBL
'''

mesonet_vars = ['STID', 'STNM', 'TIME', 'RELH', 'TAIR', 'WSPD', 'WVEC', 'WDIR',
    'WDSD', 'WSSD', 'WMAX', 'RAIN', 'PRES', 'SRAD', 'TA9M', 'WS2M', 'TS10',
    'TB10', 'TS05', 'TB05', 'TS30', 'TR05', 'TR25', 'TR60', 'TR75']

def remote_mesonet_data(date_time=None, fields=None, site=None, unpack=True):
    '''
    Reads in Oklahoma Mesonet Datafile (MDF) directly from their servers.

    date_time : datetime object
        A python :class:`datetime` object specify that date and time
        for which that data should be downloaded.  For a times series
        data, this only needs to be a date.  For snapshot files, this is
        the time to the nearest five minutes.

    fields : sequence
        A list of the variables which should be returned.  See
        :func:`read_mesonet_ts` for a list of valid fields.

    site : string
        Optional station id for the data to be fetched.  This is
        case-insensitive.  If specified, a time series file will be
        downloaded.  If left blank, a snapshot data file for the whole
        network is downloaded.

    unpack : bool
        If True, the returned array is transposed, so that arguments may be
        unpacked using ``x, y, z = remote_mesonet_ts(...)``. Defaults to True.

    Returns : array
        A nfield by ntime masked array.  nfield is the number of fields
        requested and ntime is the number of times in the file.  Each
        variable is a row in the array.  The variables are returned in
        the order given in *fields*.
    '''
    import urllib2

    if date_time is None:
        import datetime
        date_time = datetime.datetime.utcnow()

    if site is None:
        data_type = 'mdf'
        #Put time back to last even 5 minutes
        date_time = date_time.replace(minute=(dt.minute - dt.minute%5),
            second=0, microsecond=0)
        fname = '%s.mdf' % date_time.strftime('%Y%m%d%H%M')
    else:
        data_type = 'mts'
        fname = '%s%s.mts' % (date_time.strftime('%Y%m%d'), site.lower())

    #Create the various parts of the URL and assemble them together
    path = '/%s/%d/%d/%d/' % (data_type, date_time.year, date_time.month,
        date_time.day)
    baseurl='http://www.mesonet.org/public/data/getfile.php?dir=%s&filename=%s'

    #Open the remote location
    datafile = urllib2.urlopen(baseurl % (path+fname, fname))

    #Read the data 
    #Numpy.loadtxt checks prohibit actually doing this, though there's no
    #reason it can't work.  I'll file a bug.  The next two lines work around it
    from cStringIO import StringIO
    datafile = StringIO(datafile.read())
    return read_mesonet_data(datafile, fields, unpack)

def read_mesonet_data(filename, fields=None, unpack=True):
    '''
    Reads Oklahoma Mesonet data from *filename*.

    filename : string or file-like object
        Location of data. Can be anything compatible with
        :func:`numpy.loadtxt`, including a filename or a file-like
        object.

    fields : sequence
        List of fields to read from file.  (Case insensitive)
        Valid fields are:
            STID, STNM, TIME, RELH, TAIR, WSPD, WVEC, WDIR, WDSD,
            WSSD, WMAX, RAIN, PRES, SRAD, TA9M, WS2M, TS10, TB10,
            TS05, TB05, TS30, TR05, TR25, TR60, TR75
        The default is to return all fields.

    unpack : bool
        If True, the returned array is transposed, so that arguments may be
        unpacked using ``x, y, z = read_mesonet_ts(...)``. Defaults to True.

    Returns : array
        A nfield by ntime masked array.  nfield is the number of fields
        requested and ntime is the number of times in the file.  Each
        variable is a row in the array.  The variables are returned in
        the order given in *fields*.
    '''
    if fields is None:
        cols = None
    else:
        cols = [mesonet_vars.index(f.upper()) for f in fields]

    data = np.loadtxt(filename, skiprows=3, usecols=cols, unpack=unpack)

    #Mask out data that are missing or have not yet been collected
    BAD_DATA_LIMIT = -990
    return MaskedArray(data, mask=data < BAD_DATA_LIMIT)

def mesonet_stid_info(info):
    'Get mesonet station information'
    names = ['stid', 'lat', 'lon']
    dtypes = ['S4','f8','f8']
    sta_table = np.loadtxt('geomeso.csv', skiprows=123, usecols=(1,7,8),
        dtype=zip(names,dtypes), delimiter=',')
    return sta_table

#    station_indices = sta_table['stid'].searchsorted(data['stid'])
#    lat = sta_table[station_indices]['lat']
#    lon = sta_table[station_indices]['lon']

if __name__ == '__main__':
    import datetime
    from optparse import OptionParser

    import matplotlib.pyplot as plt
    from metpy.vis import meteogram

    #Create a command line option parser so we can pass in site and/or date
    parser = OptionParser()
    parser.add_option('-s', '--site', dest='site', help='get data for SITE',
        metavar='SITE', default='nrmn')
    parser.add_option('-d', '--date', dest='date', help='get data for YYYYMMDD',
        metavar='YYYYMMDD', default=None)
    
    #Parse the command line options and convert them to useful values
    opts,args = parser.parse_args()
    if opts.date is not None:
        dt = datetime.datetime.strptime(opts.date, '%Y%m%d')
    else:
        dt = None
    
    time, relh, temp, wspd, press = remote_mesonet_data(dt,
        ['time', 'relh', 'tair', 'wspd', 'pres'], opts.site)
    
    meteogram(opts.site, dt, time=time, relh=relh, temp=temp, wspd=wspd,
        press=press)

    plt.show()