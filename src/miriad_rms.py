#!/opt/caastro/ext/anaconda/bin/python

# based on examples
# http://docs.astropy.org/en/stable/io/fits/ 
# https://python4astronomers.github.io/astropy/fits.html

from __future__ import print_function
import time
start_time0=time.time()

import astropy.io.fits as pyfits
import math
import numpy as np
import sys
import os
from optparse import OptionParser,OptionGroup
from astropy.time import Time


def parse_options():
   usage="Usage: %prog [options]\n"
   usage+='\tCalculate RMS\n'
   parser = OptionParser(usage=usage,version=1.00)
   parser.add_option('-t','--threshold',dest="threshold",default=5, help="Threshold to find sources (expressed in sigmas) [default %default sigma]",type="float")
   parser.add_option('-f','--fits_type',dest="fits_type",default=0, help="FITS file type 0-single x,y image, 1-multi-axis [default %default]",type="int")
   parser.add_option('-w','--window',nargs = 4, dest="window", help="Window to calculate RMS [default %default]",type="int")   
   parser.add_option('-r','--regfile',action="store_true",dest="save_regfile",default=False, help="Save regfile with found pixels [default %default]")
   parser.add_option('--x',dest="position_x",default=-1,help="X coordinate to calculate RMS around [default %default]",type="int")
   parser.add_option('--y',dest="position_y",default=-1,help="Y coordinate to calculate RMS around [default %default]",type="int")
   parser.add_option('--center','--around_center',dest="around_center",action="store_true",default=False,help="In specified radius around the center [default %default]")
   parser.add_option('--radius',dest="radius",default=1,help="Radius to calculate RMS around (X,Y) passed in -x and -y options [default %default]",type="int")
   parser.add_option('--plotname',dest="plotname",default=None,help="Png file name if plot is required too [default %default]",type="string")
   parser.add_option('--outfile',dest="outfile",default="rms.txt",help="Output file [default %default]",type="string")
   (options, args) = parser.parse_args()
   return (options, args)


def rms_base( data, x_size, y_size, radius, window=None, border=1 ) :
   # calculate MEAN/RMS :
   # TODO : change to numpy.std() , numpy.mean()
   sum=0
   sum2=0
   count=0
   max_value=-1e20
   for y_c in range(border,y_size-border) :   
      for x_c in range(border,x_size-border) : 
         if window is None or (x_c >=window[0] and x_c <= window[2] and y_c >= window[1] and y_c <= window[3]) :      
            count_test=0
            final_value=data[y_c,x_c]
            # for y in range (y_c-radius,(y_c+radius+1)):   
            #   for x in range (x_c-radius,(x_c+radius+1)):                              
            #      value = data[y,x]
            #      final_value = final_value + value
            #      count_test = count_test + 1
            #      
            # final_value = final_value / count_test
            sum = sum + final_value
            sum2 = sum2 + final_value*final_value
            count = count + 1 
            
            if final_value > max_value :
               max_value= final_value
                        
            # print "count_test = %d" % (count_test)
   
   mean_val = (sum/count)
   rms = math.sqrt(sum2/count - mean_val*mean_val)
   print("%s : mean +/- rms = %.4f +/- %.4f (based on %d points) [vs. AUTO VALUES %.4f +/- %.4f]" % (fitsname,mean_val,rms,count,data.mean(),data.std()))
   median = -1000
   iqr    = -1000
   rms_iqr = -1000

   window_string = "(%d,%d)-(%d,%d)" % (window[0],window[1],window[2],window[3])
   
   return (mean_val,rms,max_value,count,median,iqr,rms_iqr,window_string)

def rms_around_base( data, x_size, y_size, radius, x_c=None, y_c=None, window=None, save_to_file=None, debug=True, fitsname="" ) :
   # calculate MEAN/RMS :
   # TODO : change to numpy.std() , numpy.mean()
   out_f = None
   if save_to_file is not None :
      out_f = open( save_to_file, "w" )

   if x_c is None or x_c < 0 :
      x_c = int( x_size / 2 )

   if y_c is None or y_c < 0 :
      y_c = int( y_size / 2 )
      
   if window is not None :
      x_c = (window[0] + window[2])/2
      y_c = (window[1] + window[3])/2
      
      print("DEBUG : overwritting center of RMS calculation with center of window at (%d,%d)" % (x_c,y_c))

   print("DEBUG : calculating RMS around pixel (%d,%d)" % (x_c,y_c))

   sum=0
   sum2=0
   count=0
   max_value=-1e20
   values=[]
   for y in range( int(y_c-radius) , int(y_c+radius+1) ) :   
      for x in range( int(x_c-radius) , int(x_c+radius+1) ) : 
         if window is None or (x_c >=window[0] and x_c <= window[2] and y_c >= window[1] and y_c <= window[3]) :
            dist = math.sqrt( (x-x_c)**2 + (y-y_c)**2 )

            if dist <= radius : 
               final_value=data[y,x]

               sum = sum + final_value
               sum2 = sum2 + final_value*final_value
               if final_value > max_value :
                  max_value = final_value
               count = count + 1 
               
               values.append( final_value )

               # print "count_test = %d" % (count_test)
   
   values=np.array(values)
   values.sort()
   median = values[ int(values.shape[0]/2) ]
   q75= int(len(values)*0.75);
   q25= int(len(values)*0.25);
   iqr = values[q75] - values[q25] 
   rms_iqr = iqr/1.35;

   mean_val = (sum/count)
   rms = math.sqrt(sum2/count - mean_val*mean_val)
   if debug : 
      print("\t%s : rms_around_base(%d,%d,radius=%d) mean +/- rms = %.4f +/- %.4f (based on %d points) [vs. AUTO VALUES %.4f +/- %.4f] , max_value = %.4f" % ( fitsname,x_c,y_c,radius,mean_val,rms,count,data.mean(),data.std(),max_value))

   if out_f is not None :
      out_f.close()

   window = "(%d,%d)-radius=%d" % (x_c,y_c,radius)

   return (mean_val,rms,max_value,count,median,iqr,rms_iqr,window)



def rms_func( fitsname, radius, window, save_regfile=None, around_center=False, x_c=None, y_c=None ) :
   fits = pyfits.open( fitsname )
   x_size = fits[0].header['NAXIS1']  
   y_size = fits[0].header['NAXIS2']              
   x_center = int(x_size/2)
   y_center = int(y_size/2)
   
   if x_c is None :
      x_c = x_center

   if y_c is None :
      y_c = y_center
   
   if around_center :
      if window is None :
         window = np.zeros(4)
      # option around_center overwrites window
      window[0] = x_center - radius
      window[1] = y_center - radius
      window[2] = x_center + radius + 1
      window[3] = y_center + radius + 1
      
      print("Automatically calculated window around center (%d,%d)-(%d,%d)" % (window[0],window[1],window[2], window[3]))
   
   try :
      dateobs=fits[0].header['DATE-OBS']
      t=Time(dateobs)
      t_unix=t.replicate(format='unix')
   except :
      print("WARNING : DATE-OBS keyword not found in this file %s" % (fitsname))
                     
   print() 
   print('# \tRead fits file %s of size %d x %d , data.ndim = %d , (x_c,y_c) = (%d,%d)' % (fitsname,x_size,y_size,fits[0].data.ndim,x_c,y_c))

   data = None
#   if fits_type == 1 :
   if fits[0].data.ndim >= 4 :
      print("data.ndim >= 4 -> data = fits[0].data[0,0]")
      data = fits[0].data[0,0]
   else :
      print("data.ndim < 4  -> data = data=fits[0].data")
      data=fits[0].data

   (mean_val,rms,max_value,count,median,iqr,rms_iqr,used_window) = rms_around_base( data, x_size, y_size, radius, window=window, x_c=x_c, y_c=y_c, fitsname=fitsname )

   f_reg=None
   regfile=None
   if save_regfile :
      regfile = fitsname.replace('.fits', '.reg')
      f_reg = open( regfile , "w" )

      txtfile=fitsname.replace('.fits', '.txt')
      f_txt = open( txtfile , "w" )
   for y in range(0,y_size) :   
      for x in range(0,x_size) : 
         if window is None or (x >=window[0] and x <= window[2] and y >= window[1] and y <= window[3]) :
            value = data[y,x]
          
            if value > mean_val + threshold*rms :            
               if f_reg :
                  f_reg.write( "circle %d %d 5 # %.2f Jy\n" % (x,y,value) )
                  f_txt.write( "%d %d %.2f = %.2f sigma > %.2f x %.2f\n" % (x,y,value,(value/rms),threshold,rms) )


   if f_reg : 
      f_reg.close()
      f_txt.close()
   else :
      print("WARNING : saving of .reg and .txt files was not required !")

   fits.close()

   return (mean_val,rms,t_unix.value,used_window,median,iqr,rms_iqr)


if __name__ == '__main__':
   start_time = time.time()
   print("miriad_rms.py : import took %.6f [seconds]" % (start_time-start_time0))


   # ls wsclean_timeindex???/wsclean_1192530552_timeindex8-000?-I-dirty.fits > list_for_dedisp
   listname="list_for_dedisp"
   if len(sys.argv) > 1: 
      listname = sys.argv[1]

   (options, args) = parse_options()

   if options.outfile is None :
      options.outfile = "rms_XX.txt"
      if listname.find("_YY") >= 0 :
         options.outfile = "rms_YY.txt"

   threshold=options.threshold
   fits_type=options.fits_type

   window=None
   if options.window is not None : 
      window=np.zeros(4)
      window[0]=0
      window[1]=0
      window[2]=1e6
      window[3]=1e6   
   
      window[0] = options.window[0]
      window[1] = options.window[1]
      window[2] = options.window[2]
      window[3] = options.window[3]

   if options.position_x>=0 and options.position_y>=0 and options.radius>0 :
      window[0] = options.position_x - options.radius
      window[1] = options.position_y - options.radius
   
      window[2] = options.position_x + options.radius
      window[3] = options.position_y + options.radius
   


   print("####################################################")
   print("PARAMTERS :")
   print("####################################################")
   print("fits_type = %d" % (fits_type))
   print("plotname  = %s" % (options.plotname))
   print("Center position = (%d,%d) , radius = %d" % (options.position_x,options.position_y,options.radius))
   if options.window is not None :
      print("window    = (%d,%d)-(%d,%d)" % (window[0],window[1],window[2],window[3]))   
   print("Automatic center calculation = %s" % (options.around_center))
   print("####################################################")


   if listname.find(".fits") >= 0 :
      f_tmp = open( "list_tmp" , "w" )
      f_tmp.write( ("%s\n" % listname) )
      f_tmp.close()
      listname="list_tmp"
      print("Processing single FITS file, written fits file %s to temporary list file list_tmp" % (listname))

   radius = options.radius
   threshold_in_sigma=3
   max_rms=1.00

   # x_c=250
   # if len(sys.argv) > 1:
   #   x_c = int(sys.argv[1])

#   outdir="dedispersed/"
#   os.system("mkdir -p dedispersed/")

   f = open (listname,"r")
   out_f = None
   if options.outfile is not None :
      b_header = True
      if os.path.exists( options.outfile ) :
         b_header = False

      out_f = open( options.outfile , "a+" )
   
      if b_header :
         out_f.write("# UNIXTIME RMS MEAN_VALUE FILE_NAME RADIUS WINDOW_IF_SPECIFIED MEDIAN RMS_IQR IQR\n")

   values=[]
   while 1:
      fitsname = f.readline().strip()
      unixtime = 0

      if not fitsname: 
         break
      
      # wsclean_timeindex008/wsclean_1192530552_timeindex8-0001-I-dirty.fits
      # timeidx=int(fitsname[17:20])
      # cc=int(fitsname[-17:-13])      

      (mean_val , rms, unixtime, used_window, median, iqr, rms_iqr ) = rms_func( fitsname, radius=radius, window=window, save_regfile=options.save_regfile, around_center=options.around_center, x_c=options.position_x, y_c=options.position_y  )

      values.append(rms)
   
      if out_f is not None :
         line = "%.2f %.8f %.8f %s %d %s %.4f %.4f %.4f\n" % (unixtime,rms,mean_val,fitsname,radius,used_window,median, rms_iqr, iqr)
         out_f.write( line )
   
      # NEW :
      # mean_new = data.mean()
      # rms_new  = data.std()
      # print "NEW : mean +/- rms = %.4f +/- %.4f" % (mean_new,rms_new)

   if out_f is not None :
      out_f.close()
   
   if options.plotname is not None and len(values)>0 :
      from histofile import histoarray
      values_np = np.array(values)
      histoarray(values_np,n_bin=100,filename=options.plotname)


   f.close()

   end_time = time.time()
   print("miriad_rms.py: Start_time = %.6f , end_time = %.6f -> took = %.6f seconds (including import took %.6f seconds)" % (start_time,end_time,(end_time-start_time),(end_time-start_time0)))

