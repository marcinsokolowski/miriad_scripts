#!/usr/bin/python

from __future__ import print_function
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import matplotlib.pyplot as plt  
import matplotlib.mlab as mlab
import sys
import os,errno
from pylab import *
# import plotly.plotly as py # pip install plotly
import chart_studio.plotly as py # pip install chart_studio
from array import *
import astropy.io.fits as pyfits
import optparse


def mkdir_p(path):
   try:
      os.makedirs(path)
   except OSError as exc: # Python >2.5
      if exc.errno == errno.EEXIST:
         pass
   else:
      pass

def is_number(s):
    """ Returns True is string is a number. """
    try:
        float(s)
        return True
    except ValueError:
        return False

def histoarray(x,n_bin=100,filename="unknown",pngfile="unknown.png",x_axis_desc="Flux density [Jy]",options_low=None,options_up=None) :
   fig=plt.figure()

   mean=x.mean()
   rms=x.std()

   low = mean - 10*rms
   up  = mean + 10*rms

   if options_low is not None : 
      low = options_low 
      
   if options_up is not None : 
      up = options_up


   print("File : %s" % (filename))
   print("MEAN = %.8f" % (mean))
   print("RMS  = %.8f" % (rms))
   print("Histogram limits = %.8f - %.8f" % (low,up))

   n, bins, patches = plt.hist(x, n_bin, normed=1, facecolor='blue', alpha=0.5, range=[low,up])
   
   n = np.array(n)
   n = n[np.logical_not(np.isnan(n))]
      
   # add a 'best fit' line
   y = mlab.normpdf(bins, mean, rms)
   plt.plot(bins, y, 'r--')

   # Tweak spacing to prevent clipping of ylabel
   # plt.subplots_adjust(left=0.15)
   # plot_url = py.plot_mpl(fig, filename='docs/histogram-mpl-legend')

   # plt.plot(freqs,powers)

   plt.xlabel(x_axis_desc)
   plt.ylabel('Number of counts') 
   plt.text((low+up)*0.5,n.max()*0.75,'RMS = ' + str(rms))
   plt.text((low+up)*0.5,n.max()*0.70,'MEAN = ' + str(mean))

   if options_low is not None and options_up is not None :
      x_1d_1=x[x>=low]
      x_1d_2=x_1d_1[x_1d_1<=up]
      
      mean2 = x_1d_2.mean()
      rms2  = x_1d_2.std()
      plt.text((low+up)*0.5,n.max()*0.95,'RMS and MEAN in range %.2f - %.2f' % (options_low,options_up))
      plt.text((low+up)*0.5,n.max()*0.90,'RMS = ' + str(rms2))
      plt.text((low+up)*0.5,n.max()*0.85,'MEAN = ' + str(mean2))


   # plt.yscale('log')
   # plt.ylim(ymin=1,ymax=np.max(powers)*1.1)
   # plt.ylim(ymin=1,ymax=np.max(powers)*1.1)
   # plt.xlim(xmin=0)
   plt.title(filename)
   # plt.show()
   plt.savefig(pngfile)


if __name__ == '__main__': 
   filename="v.txt"
   if len(sys.argv) > 1:   
      filename = sys.argv[1]

   parser=optparse.OptionParser()
   parser.set_usage("""histofits.py FITS""")
   parser.add_option("--n_bin","--n_bins",dest="n_bin",default=100,help="Number of bints [default: %default]",type="int")
   parser.add_option("--low","-l",dest="low",default=None,help="Number of bints [default: %default]",type="float")
   parser.add_option("--up","-u",dest="up",default=None,help="Number of bints [default: %default]",type="float")
   parser.add_option("-x","--x_axis",'--x_axis_desc',dest="x_axis_desc",default="Flux density [Jy]",help="X axis value [default: %default]")
   parser.add_option("-y","--y_axis",'--y_axis_desc',dest="y_axis_desc",default="Number of counts",help="Number of bins [default: %default]")
   parser.add_option("--column","--col","-c",dest="column",default=0,help="Column index (starting from 0) to be histogramed [default: %default]",type="int")
   parser.add_option("-p","--pngfile",'--image',dest="pngfile",default=None,help="Pngfile [default: %default]")
   (options,args)=parser.parse_args(sys.argv[1:])

   mkdir_p("images/")   

   # alldata = loadtxt(filename,delimiter=' ',usecols='1')
   #plot columns 2 to : against column 1
   # x=(data[:,0])
   # y=(data[:,1])

   # print "DATA : %d-%d" % (alldata[0],alldata[2047])

   x=None
   pngfile = options.pngfile
   
   if filename.find(".fits") >= 0 :
     if pngfile is None :
         pngfile = 'images/' + filename.replace('.fits', '.png' )
     fits = pyfits.open( filename )
     x_size=fits[0].header['NAXIS1']  
     y_size=fits[0].header['NAXIS2']

     data = None
     if fits[0].data.ndim >= 4 :
        data = fits[0].data[0,0]
     else :
        data=fits[0].data

     x=np.ndarray.flatten(data)
     fits.close()
   else :
     if pngfile is None :
         pngfile='images/' + filename.replace('.txt', '.png' )
     try :
        alldata = loadtxt(filename)
     except :
        print("ERROR : when reading file %s -> trying traditional way ..." % (filename))
        alldata_list=[]
         
        file=open(filename,'r')
        # reads the entire file into a list of strings variable data :
        data=file.readlines()

        for line in data : 
           words = line.split(' ')

           if line[0] == '#' :
              continue

           if line[0] != "#" and is_number(words[options.column]) :               
              x=float(words[options.column])
              alldata_list.append(x)
           else :
              print("WARNING : %s skipped as non-digit (%s)" % (words[options.column],words[options.column].isdigit()))
         
        file.close()

        print("len(alldata_list) = %d" % (len(alldata_list)))         
        alldata = np.asarray( alldata_list )
         
         
     print("Data in '%s' has %d rows" % (filename,alldata.shape[0]))   
     x=alldata
#     print "%s" % (x)
      
   # if alldata.ndim >= 2 :
   #   x=alldata[:,
   histoarray(x,n_bin=options.n_bin,filename=filename,pngfile=pngfile,x_axis_desc=options.x_axis_desc,options_low=options.low,options_up=options.up)

