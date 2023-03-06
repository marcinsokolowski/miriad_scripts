#!/opt/caastro/ext/anaconda/bin/python

# based on examples
# http://docs.astropy.org/en/stable/io/fits/ 
# https://python4astronomers.github.io/astropy/fits.html

from __future__ import print_function

import time
start_time0=time.time()


import astropy.io.fits as pyfits
import math
import numpy
import sys
import pix2sky;
import skysources
import miriad_rms
from optparse import OptionParser,OptionGroup
import datetime



def parse_options(idx):
   usage="Usage: %prog [options]\n"
   usage+='\tShown known sources \n'
   parser = OptionParser(usage=usage,version=1.00)
#   parser.add_option('-a','--a_team','--ateam','--a_team_sources',action="store_true",dest="check_ateam_sources", default=True, help="Check A-team sources [default %default]")
#   parser.add_option('-r','--a_team_radius','--aradius','--a_team_sources_radius',dest="a_team_sources_radius", default=3.8, help="A-team sources radius [deg] should be at least 1 beam size [default %default is beam size at 150 MHz]")
#   parser.add_option('-s','--sun_radius','--sradius','--sunradius',dest="sun_radius", default=8, help="Sun radius [deg] might even be 10 degrees [default %default is ~2 beam sizes at 150 MHz]")
#   parser.add_option('-t','--threshlold','--thresh_in_sigma',dest="threshold_in_sigma", default=5, help="Thresholod in sigma [default %default]",type="float")
   
#   parser.add_option('-m','--mean_cc',action="store_true",dest="mean_cc",default=True, help="Mean of coarse channels [default %]")
#   parser.add_option('--no_mean_cc',action="store_false",dest="mean_cc",default=True, help="Turn off calculation of mean of coarse channels [default %]")
#   parser.add_option('-o','--outdir',dest="outdir",default=None, help="Output directory [default %]")
#   parser.add_option('--meta_fits','--metafits',dest="metafits",default=None, help="Metafits file [default %]")
   parser.add_option('--add_extension','--add_ext','--postfix','--ext',dest="add_extension",default=None, help="Add extension to values in list file [default None]")

   (options, args) = parser.parse_args(sys.argv[idx:])

   return (options, args)



def find_source( x, y, list_x, list_y, radius=5 ):
   if len(list_x) != len(list_y) :
      print("ERROR : wrong list sizes !!!")
      return -1


   for i in range(0,len(list_x)) :
      x_ref = list_x[i]
      y_ref = list_y[i]
      
      if math.fabs(x-x_ref)<radius and math.fabs(y-y_ref)<radius :
         return i
         
   return -1

if __name__ == '__main__':
   start_time = time.time()
   print("show_known_sources : imports took %.6f [seconds]" % (start_time-start_time0))

   # ls wsclean_timeindex???/wsclean_1192530552_timeindex8-000?-I-dirty.fits > list_for_dedisp
   listname="test.fits"
   if len(sys.argv) > 1: 
      listname = sys.argv[1]

   (options, args) = parse_options(1) 

   print("##############################################################")
   print("PARAMETERS :")
   print("##############################################################")
   print("listfile                       = %s" % (listname))
   print("add_extension                  = |%s|" % (options.add_extension))
   print("##############################################################")

   fits_list=[]
   if listname.find(".fits") >= 0 :
      print("Treating listname = %s as a single fits file" % (listname))
      fits_list.append( listname )
   else :
      print("Listname = %s is list of fits files" % (listname))
      f = open (listname,"r")
      while 1:
         fitsname = f.readline().strip()
         if not fitsname: 
            break

         
         if options.add_extension is not None :
            fitsname = fitsname + options.add_extension
            
         fits_list.append( fitsname )
         print("Added %s" % (fitsname))
      
      f.close()
      print("Read fits files from list file")
   


   for fitsname in fits_list :
      fits = pyfits.open( fitsname )
      x_size = int( fits[0].header['NAXIS1'] )
      y_size = int( fits[0].header['NAXIS2'] )
      print() 
      print('# Read fits file %s of size %d x %d' % (fitsname,x_size,y_size))

      if fits[0].data.ndim >= 4 :
         data = fits[0].data[0,0]
      else :
         data=fits[0].data


      postfix_txt = ("_known_sources.txt")
      postfix_reg = ("_known_sources.reg")


      regfile=fitsname.replace('.fits', postfix_reg )
      txtfile=fitsname.replace('.fits', postfix_txt )
      f_reg = open( regfile , "w" )   
      f_txt = open( txtfile , "w" )
      f_reg.write("global color=white width=3 font=\"times 30 normal\"\n")
   
      known_sources = skysources.GetKnownSources()
      for src in known_sources :
         (x,y) = pix2sky.sky2pix( fits, src.ra_degs, src.dec_degs, fitsname=fitsname ) 

         if not numpy.isnan(x) and not numpy.isnan(y) :
            print("%s : (ra,dec) = (%.4f,%.4f) [deg] -> (x,y) = (%d,%d)" % (src.name,src.ra_degs,src.dec_degs,x,y))
         
#            f_reg.write( "circle %d %d %d # text={%s at (ra,dec) = (%.4f,%.4f) [deg]}\n" % ((x+1),(y+1),10,src.name,src.ra_degs,src.dec_degs) )
            f_reg.write( "circle %d %d %d # text={%s}\n" % ((x+1),(y+1),10,src.name) )
#            f_reg.write( "text %d %d text={%s}\n" % ((x+5),(y+15),src.name) )
#            f_reg.write( "text %d %d {%s}\n" % ((x+5),(y+15),src.name) )
         else :
            print("%s : (ra,dec) = (%.4f,%.4f) [deg] -> NaN (outside image)" % (src.name,src.ra_degs,src.dec_degs))
   
   
      f_reg.close()
      f_txt.close()
   
   end_time = time.time()
   print("show_known_sources : Start_time = %.6f , end_time = %.6f -> took = %.6f seconds (including import took %.6f seconds)" % (start_time,end_time,(end_time-start_time),(end_time-start_time0)))
