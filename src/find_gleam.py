from __future__ import print_function
import numpy as np
import astropy.wcs as wcs
import astropy.io.fits as pf
from astropy import units as au
from astropy.coordinates import SkyCoord
from astropy.coordinates import Angle
from astropy.table import Table
import ephem
import os
import glob
import datetime
import pytz
import sys
import scipy.linalg
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
from astropy import units as u
import math
from optparse import OptionParser,OptionGroup

try:
    import astropy.io.fits as pyfits
    import astropy.wcs as pywcs
    _useastropy=True
except ImportError:
    import pywcs,pyfits
    _useastropy=False


# Example of checking a source in the image in the GLEAM catalog :
# import find_gleam
# (RA,Dec,gleam_sources,gleam_fluxes,radius) = find_gleam.get_gleam_sources( "avg_I.fits" )
# s=find_gleam.find_source(gleam_sources,gleam_fluxes,97.2166,-28.9391) 
#
# Example of matching the sources from the text file list to GLEAM catalog :
# find_gleam.calibrate_image("avg_I_without.fits","avg_I_without.txt")
# avg_I_without.txt - format : X Y RA[deg] DEC[deg] Peak_Flux[Jy/Beam]

# Constants
C = 2.99792458e8
r2h = 12.0/np.pi
r2d = 180.0/np.pi
h2d = 360.0/24.0
d2h = 24.0/360.0
ARCMIN2RAD = np.pi / (60.0 * 180.0)
DEG2RAD = ( math.pi / 180.00)
RAD2DEG = ( 180.00 / math.pi )
RAD2ARCSEC = ( ( 180.00 / math.pi )*3600. )

gleam_default_file="/home/msok/MWA_Tools/catalogues/GLEAM_EGC.fits"
g_debug_level=0

class ImageSource :
   x=-1
   y=-1
   ra=0
   dec=0
   peak_flux=0

   def __init__(self, x, y, ra, dec, peak_flux):
        self.x = x
        self.y = y
        self.ra = ra
        self.dec = dec
        self.peak_flux = peak_flux



def find_gleam( ra, dec, radius_arcsec=60, freq_cc=145, min_flux=0.00 ) :
   gleam_path=gleam_default_file
   if not os.path.exists( gleam_path ) :
      gleam_path = "GLEAM_EGC.fits"
      
   sin_ra  = math.sin(ra*DEG2RAD)
   sin_dec = math.sin(dec*DEG2RAD)
   cos_dec = math.cos(dec*DEG2RAD)      

   gleam_freq = {}
   gleam_freq["069"] = ["peak_flux_076", "peak_flux_084", "peak_flux_092", "peak_flux_099", 87.68]
   gleam_freq["093"] = ["peak_flux_107", "peak_flux_115", "peak_flux_122", "peak_flux_130", 118.4]
   gleam_freq["121"] = ["peak_flux_143", "peak_flux_151", "peak_flux_158", "peak_flux_166", 154.24]
   gleam_freq["145"] = ["peak_flux_174", "peak_flux_181", "peak_flux_189", "peak_flux_197", 184.96]
   gleam_freq["158"] = ["peak_flux_204", "peak_flux_212", "peak_flux_220", "peak_flux_227",  202.24]
   gleam_freq["169"] = ["peak_flux_204", "peak_flux_212", "peak_flux_220", "peak_flux_227", 215.68]


   freq_str=("%03d" % freq_cc)
   freqs = None
   if freq_str in gleam_freq.keys() :
       freqs = gleam_freq[freq_str]
   else :
       min_diff = 1e20
       best_freq = "-1"
       for f in gleam_freq.keys() :
           diff = int(f) - freq_cc
           if math.fabs(diff) < min_diff :
               min_diff = math.fabs(diff)
               best_freq = f
       
       if int(best_freq) > 0 :
           print("WARNING : could not find frequency %s -> using closest frequency %s" % (freq_str,best_freq))
           freqs = gleam_freq[best_freq]
       else :
           print("ERROR : error in code ??? non frequency is close to %s ???" % (freq_str))
           os.exit(-1)
           
   
   
   print("Looking for GLEAM sources around (ra,dec) = (%.4f,%.4f) [deg] +/- %.2f [arcsec] around channel %s" % (ra,dec,radius_arcsec,freq_str))
   
   fov = radius_arcsec/3600.00
   decmin = dec - fov
   decmax = dec + fov
   window = 100
   gleam = Table.read( gleam_path )
   print("Selecting sources with flux > %.2f Jy, and DEC : %.2f deg < DEC < %.2f deg (dec = %.2f +/- %.2f [deg])" % (min_flux,decmin,decmax,dec,fov))
   sfluxes = (gleam[freqs[0]]+gleam[freqs[1]]+gleam[freqs[2]]+gleam[freqs[3]])/4.0
#   sfluxes = (gleam[freqs[0]]+gleam[freqs[1]]+gleam[freqs[2]])/3.0
#   sources = np.where((sfluxes > smin) & (gleam["DEJ2000"] > decmin) & (gleam["DEJ2000"] < decmax))
#   sources = np.where((gleam["DEJ2000"] > decmin) & (gleam["DEJ2000"] < decmax) & (((gleam[freqs[0]]+gleam[freqs[1]]+gleam[freqs[2]]+gleam[freqs[3]])/4.0)>smin) )
   sources = np.where((gleam["DEJ2000"] > decmin) & (gleam["DEJ2000"] < decmax))
   radegs = np.array(gleam["RAJ2000"][sources])
   decdegs = np.array(gleam["DEJ2000"][sources])
   fluxes_174 = np.array(gleam["peak_flux_174"][sources])
   fluxes_181 = np.array(gleam["peak_flux_181"][sources])
   fluxes_189 = np.array(gleam["peak_flux_189"][sources])
   fluxes_197 = np.array(gleam["peak_flux_197"][sources])

   if math.fabs(freq_cc-69) < 10 :
       print("INFO : using fluxes around channel 69")
       fluxes_174 = np.array(gleam["peak_flux_076"][sources])
       fluxes_181 = np.array(gleam["peak_flux_084"][sources])
       fluxes_189 = np.array(gleam["peak_flux_092"][sources])
       fluxes_197 = np.array(gleam["peak_flux_099"][sources])

   fluxes = ( fluxes_174 + fluxes_181 + fluxes_189 + fluxes_197 ) / 4.00

   sc = SkyCoord(Angle(radegs * au.deg), Angle(decdegs * au.deg), frame='fk5')
 
   condition = fluxes>min_flux
   out_sc_tmp = sc[condition]
   out_fluxes_tmp = fluxes[condition]


   # cos_x = math.sin(dec_rad)*sin_dec_find_ra + math.cos(dec_rad)*cos_dec_find_ra*math.cos( ra_rad - ra_find_rad )
   # dist_rad = math.acos( cos_x );
   # dist_arcsec = dist_rad * RAD2ARCSEC
   distances_cos = np.sin(out_sc_tmp.dec.value*DEG2RAD)*sin_dec + np.cos(out_sc_tmp.dec.value*DEG2RAD)*cos_dec*np.cos( (out_sc_tmp.ra.value-ra)*DEG2RAD )
   distances_arcsec = np.arccos( distances_cos) * RAD2ARCSEC
   condition_distance = distances_arcsec < radius_arcsec   
   out_sc = out_sc_tmp[condition_distance]
   out_fluxes = out_fluxes_tmp[condition_distance]
   out_distances_arcsec = distances_arcsec[condition_distance]

   
#   out_sc = []
#   out_fluxes = []
#   i=0
#   for s in sc :
#      if fluxes[i] > min_flux :
#         out_sc.append( sc[i] )         
#         out_fluxes.append( fluxes[i] )
#      i = i + 1
#      
#   
##   return (sc,fluxes)
   print("find_gleam returns %d sources" % (len(out_sc)))

   return (out_sc,out_fluxes,out_distances_arcsec)


def dump_gleam( outfile = "gleam_dump.txt" ) :
   gleam_path=gleam_default_file
   if not os.path.exists( gleam_path ) :
      gleam_path = "GLEAM_EGC.fits"

   gleam = Table.read(  gleam_path )
   names = gleam['Name']
   peak_flux_174 = gleam["peak_flux_174"]
   peak_flux_181 = gleam["peak_flux_181"]
   peak_flux_189 = gleam["peak_flux_189"]
   peak_flux_197 = gleam["peak_flux_197"]
   peak_flux_avg = (peak_flux_174+peak_flux_181+peak_flux_189+peak_flux_197)/4.00
   
   int_flux_174 = gleam["int_flux_174"]
   int_flux_181 = gleam["int_flux_181"]
   int_flux_189 = gleam["int_flux_189"]
   int_flux_197 = gleam["int_flux_197"]
   int_flux_avg = (int_flux_174+int_flux_181+int_flux_189+int_flux_197)/4.00
   
   len = names.size   
   outf = open(outfile,"w")
   for i in range(0,len) :
      line = "%s %.4f %.4f %.4f %.4f %.4f %.4f %.4f %.4f %.4f %.4f\n" % (names[i],peak_flux_avg[i],int_flux_avg[i],peak_flux_174[i],peak_flux_181[i],peak_flux_189[i],peak_flux_197[i],int_flux_174[i],int_flux_181[i],int_flux_189[i],int_flux_197[i])
      outf.write(line)
   
   outf.close()
   
   return (len)
   
def gleam2sql( outfile = "gleam.sql" , pidb=True, max_dec=-40.3737  ) : # max_dec=-40.3737 for NVSS
# TGSS : max_dec=-53.00 ) :  # -53.00 to read only below min declination of TGSS (otherwise should be 90.00 )
   gleam_path=gleam_default_file
   if not os.path.exists( gleam_path ) :
      gleam_path = "GLEAM_EGC.fits"

   gleam = Table.read(  gleam_path )
   names = gleam['Name']
   
   gleam_freq = {}
   gleam_freq["069"] = ["peak_flux_076", "peak_flux_084", "peak_flux_092", "peak_flux_099", 87.68]
   gleam_freq["093"] = ["peak_flux_107", "peak_flux_115", "peak_flux_122", "peak_flux_130", 118.4]
   gleam_freq["121"] = ["peak_flux_143", "peak_flux_151", "peak_flux_158", "peak_flux_166", 154.24]
   gleam_freq["145"] = ["peak_flux_174", "peak_flux_181", "peak_flux_189", "peak_flux_197", 184.96]
   gleam_freq["158"] = ["peak_flux_204", "peak_flux_212", "peak_flux_220", "peak_flux_227",  202.24]
   gleam_freq["169"] = ["peak_flux_204", "peak_flux_212", "peak_flux_220", "peak_flux_227", 215.68]

   flux_69 = (gleam["peak_flux_076"]+gleam["peak_flux_084"]+gleam["peak_flux_092"]+gleam["peak_flux_099"])/4.0
   flux_93 = (gleam["peak_flux_107"]+gleam["peak_flux_115"]+gleam["peak_flux_122"]+gleam["peak_flux_130"])/4.0
   flux_121 = (gleam["peak_flux_143"]+gleam["peak_flux_151"]+gleam["peak_flux_158"]+gleam["peak_flux_166"])/4.0
   flux_145 = (gleam["peak_flux_174"]+gleam["peak_flux_181"]+gleam["peak_flux_189"]+gleam["peak_flux_197"])/4.0
   flux_169 = (gleam["peak_flux_204"]+gleam["peak_flux_212"]+gleam["peak_flux_220"]+gleam["peak_flux_227"])/4.0

   
   peak_flux_174 = gleam["peak_flux_174"]
   peak_flux_181 = gleam["peak_flux_181"]
   peak_flux_189 = gleam["peak_flux_189"]
   peak_flux_197 = gleam["peak_flux_197"]
   peak_flux_avg = (peak_flux_174+peak_flux_181+peak_flux_189+peak_flux_197)/4.00
   
   int_flux_174 = gleam["int_flux_174"]
   int_flux_181 = gleam["int_flux_181"]
   int_flux_189 = gleam["int_flux_189"]
   int_flux_197 = gleam["int_flux_197"]
   int_flux_avg = (int_flux_174+int_flux_181+int_flux_189+int_flux_197)/4.00
 
   
   ra = gleam['RAJ2000']
   ra_err = gleam['err_RAJ2000']
   dec = gleam['DEJ2000']
   dec_err = gleam['err_DEJ2000']
   peak_flux_wide = gleam['peak_flux_wide']
   err_peak_flux_wide = gleam['err_peak_flux_wide']
   int_flux_wide = gleam['int_flux_wide']
   err_int_flux_wide = gleam['err_int_flux_wide']
   
   len = names.size   
   outf = open(outfile,"w")
   line = ""
   if pidb :
       line = "COPY STARS ( ra, dec, magnitude, name, sigma_mag, min_mag, max_mag, mag_cat, sigma_ra, sigma_dec, source_catalog, camid ) FROM stdin;\n"
   else :
      line = "COPY STARS ( ra, dec, flux, name, peak_flux_wide, int_flux_wide, flux_cat_69, flux_cat_93, flux_cat_121, flux_cat_145, flux_cat_169, ra_err, dec_err ) FROM stdin;\n"
     
   outf.write(line)

   for i in range(0,len) :
      if dec[i] < max_dec : 
         line = None 
         if pidb : 
            line = "%.4f\t%.4f\t%.4f\t'%s'\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f\t%d\t%d\n" % (ra[i],dec[i],peak_flux_avg[i],names[i],err_int_flux_wide[i],peak_flux_avg[i],peak_flux_avg[i],peak_flux_avg[i],ra_err[i],dec_err[i],1,1)
         else :
            line = "%.4f\t%.4f\t%.4f\t'%s'\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f\n" % (ra[i],dec[i],peak_flux_avg[i],names[i],peak_flux_avg[i],int_flux_avg[i],flux_69[i],flux_93[i],flux_121[i],flux_145[i],flux_169[i],ra_err[i],dec_err[i])
   
         outf.write(line)
   
   outf.close()
   
   return (len)
   
def select_gleam( ramin, ramax, decmin, decmax, freq_cc=145, min_flux=0.00 ) :
   gleam_path=gleam_default_file
   if not os.path.exists( gleam_path ) :
      gleam_path = "GLEAM_EGC.fits"

   ra = (ramin+ramax)/2.00
   dec = (decmin+decmax)/2.00
   sin_ra  = math.sin(ra*DEG2RAD)
   sin_dec = math.sin(dec*DEG2RAD)
   cos_dec = math.cos(dec*DEG2RAD)      

   gleam_freq = {}
   gleam_freq["069"] = ["peak_flux_076", "peak_flux_084", "peak_flux_092", "peak_flux_099", 87.68]
   gleam_freq["093"] = ["peak_flux_107", "peak_flux_115", "peak_flux_122", "peak_flux_130", 118.4]
   gleam_freq["121"] = ["peak_flux_143", "peak_flux_151", "peak_flux_158", "peak_flux_166", 154.24]
   gleam_freq["145"] = ["peak_flux_174", "peak_flux_181", "peak_flux_189", "peak_flux_197", 184.96]
   gleam_freq["158"] = ["peak_flux_204", "peak_flux_212", "peak_flux_220", "peak_flux_227",  202.24]
   gleam_freq["169"] = ["peak_flux_204", "peak_flux_212", "peak_flux_220", "peak_flux_227", 215.68]


   freq_str=("%03d" % freq_cc)
   freqs = gleam_freq[freq_str]

   print("Looking for GLEAM sources around in window (%.4f,%.4f)-(%.4f,%.4f) using channel %s" % (ramin,decmin,ramax,decmax,freq_str))
   
   gleam = Table.read(  gleam_path )
   sfluxes = (gleam[freqs[0]]+gleam[freqs[1]]+gleam[freqs[2]]+gleam[freqs[3]])/4.0
#   sfluxes = (gleam[freqs[0]]+gleam[freqs[1]]+gleam[freqs[2]])/3.0
#   sources = np.where((sfluxes > smin) & (gleam["DEJ2000"] > decmin) & (gleam["DEJ2000"] < decmax))
#   sources = np.where((gleam["DEJ2000"] > decmin) & (gleam["DEJ2000"] < decmax) & (((gleam[freqs[0]]+gleam[freqs[1]]+gleam[freqs[2]]+gleam[freqs[3]])/4.0)>smin) )
   sources = np.where((gleam["DEJ2000"] > decmin) & (gleam["DEJ2000"] < decmax) & (gleam["RAJ2000"] > ramin) & (gleam["RAJ2000"] < ramax))
   radegs = np.array(gleam["RAJ2000"][sources])
   decdegs = np.array(gleam["DEJ2000"][sources])
   fluxes_174 = np.array(gleam["peak_flux_174"][sources])
   fluxes_181 = np.array(gleam["peak_flux_181"][sources])
   fluxes_189 = np.array(gleam["peak_flux_189"][sources])
   fluxes_197 = np.array(gleam["peak_flux_197"][sources])
   
   if math.fabs(freq_cc-69) < 10 :
       print("INFO : using fluxes around channel 69")
       fluxes_174 = np.array(gleam["peak_flux_076"][sources])
       fluxes_181 = np.array(gleam["peak_flux_084"][sources])
       fluxes_189 = np.array(gleam["peak_flux_092"][sources])
       fluxes_197 = np.array(gleam["peak_flux_099"][sources])
       
   fluxes = ( fluxes_174 + fluxes_181 + fluxes_189 + fluxes_197 ) / 4.00


   sc = SkyCoord(Angle(radegs * au.deg), Angle(decdegs * au.deg), frame='fk5')

   condition = fluxes>min_flux
   out_sc_tmp = sc[condition]
   out_fluxes_tmp = fluxes[condition]

   # cos_x = math.sin(dec_rad)*sin_dec_find_ra + math.cos(dec_rad)*cos_dec_find_ra*math.cos( ra_rad - ra_find_rad );
   # dist_rad = math.acos( cos_x );
   # dist_arcsec = dist_rad * RAD2ARCSEC
#   distances_cos = np.sin(out_sc_tmp.dec.value*DEG2RAD)*sin_dec + np.cos(out_sc_tmp.dec.value*DEG2RAD)*cos_dec*np.cos( (out_sc_tmp.ra.value-ra)*DEG2RAD )
#   distances_arcsec = np.arccos( distances_cos) * RAD2ARCSEC
#   condition_distance = distances_arcsec < radius_arcsec
#   out_sc = out_sc_tmp[condition_distance]
#   out_fluxes = out_fluxes_tmp[condition_distance]
#   out_fluxes = None
   out_sc = out_sc_tmp
   out_fluxes = out_fluxes_tmp


#   out_sc = []
#   out_fluxes = []
#   i=0
#   for s in sc :
#      if fluxes[i] > min_flux :
#         out_sc.append( sc[i] )         
#         out_fluxes.append( fluxes[i] )
#      i = i + 1
#      
#   
##   return (sc,fluxes)
   return (out_sc,out_fluxes)


def find_source_xy( RA_map, Dec_map, source_list, flux_list, x=0, y=0, radius_arcsec=60, flux_min=0.00 ) :
   ra=RA_map[x,y]
   if ra < 0 :
      ra = ra + 360.00
      
   dec=Dec_map[x,y]
   
   print("(x,y) = (%d,%d) -> (ra,dec) = (%.4f,%.4f) [deg]" % (x,y,ra,dec))
   
   return find_source( source_list, flux_list, ra, dec, radius_arcsec=radius_arcsec, flux_min=flux_min ) 
   

      
def find_source( source_list, flux_list, ra_find=0, dec_find=0, radius_arcsec=120, flux_min=0.00 ) :
   global g_debug_level

   ra_find_rad = ra_find*DEG2RAD
   dec_find_rad = dec_find*DEG2RAD
   
   sin_dec_find_ra = math.sin(dec_find_rad)
   cos_dec_find_ra = math.cos(dec_find_rad)

   for i in range(0,len(source_list)) :
      source = source_list[i]
      flux   = flux_list[i]
      
      ra_rad = source.ra.value*DEG2RAD
      dec_rad = source.dec.value*DEG2RAD
      
      if g_debug_level > 1 :
         print("%.4f %.4f %.4f[Jy] %.4f %.4f -> dist = %.4f [arcsec]\n" % (source.ra.value,source.dec.value,flux,ra_find,dec_find,dist_arcsec))
      
      cos_x = math.sin(dec_rad)*sin_dec_find_ra + math.cos(dec_rad)*cos_dec_find_ra*math.cos( ra_rad - ra_find_rad );
      dist_rad = math.acos( cos_x );
      dist_arcsec = dist_rad * RAD2ARCSEC
      
      if dist_arcsec <= radius_arcsec and flux > flux_min:
         return (source,flux,dist_arcsec)


   return (None,None,None)

def update_fluxes( fitsname, source_list, radius=5 ) :
   fits = pyfits.open(fitsname)
   x_size=fits[0].header['NAXIS1']
   y_size=fits[0].header['NAXIS2']

   center_x = x_size/2.00
   center_y = y_size/2.00

   data=fits[0].data
   for source in source_list :
      max_val = source.peak_flux
      
      for y in range(int(source.y-radius),int(source.y+radius)) :
         for x in range(int(source.x-radius),int(source.x+radius)) :
            if y>=0 and y<y_size and x>=0 and x<x_size :
               if g_debug_level > 1 :
                  print("(%d,%d) = %.4f" % (x,y,data[x,y]))
               if data[x,y] > max_val :
                  max_val = data[x,y]
               
      if max_val > source.peak_flux :
         source.peak_flux = max_val
         
   return (source_list)         
         
      
# finds all GLEAM sources in the given FITS file :
def find_image_gleam_sources( fitsname ) :
   fits = pyfits.open(fitsname)
   x_size=fits[0].header['NAXIS1']
   y_size=fits[0].header['NAXIS2']
   freq_hz=145*1.28*1e6
   try : 
       freq_hz=fits[0].header['FREQCENT']
   except :
       print("WARNING : missing keyword FREQCENT, ignored")
   freq_cc=freq_hz/(1.28*1e6)
   

   center_x = x_size/2.00
   center_y = y_size/2.00
   
   ext=0

   h=fits[ext].header
   wcs=pywcs.WCS(h)
   naxes=h['NAXIS']
   cdelta1=h['CDELT1']
   cdelta2=h['CDELT2']
   
   cdelta=math.sqrt(cdelta1*cdelta1 + cdelta2*cdelta2)
   radius = ((math.sqrt(2.00)*x_size)/2.00)*cdelta
   
   print("naxes = %d, cdelta = %.4f [deg]" % (naxes,radius))

   x=np.arange(1,h['NAXIS1']+1)
   y=np.arange(1,h['NAXIS2']+1)

   ff=1
   Y,X=np.meshgrid(y,x)

   Xflat=X.flatten()
   Yflat=Y.flatten()
   FF=ff*np.ones(Xflat.shape)

   print("naxes = %d" % naxes)
   if naxes >= 4 :     
      Tostack=[Xflat,Yflat,FF] 
      for i in xrange(3,naxes):
         Tostack.append(np.ones(Xflat.shape))
   else :
      Tostack=[Xflat,Yflat]
   pixcrd=np.vstack(Tostack).transpose()
   
   try:
      # Convert pixel coordinates to world coordinates
      # The second argument is "origin" -- in this case we're declaring we
      # have 1-based (Fortran-like) coordinates.
  
      if _useastropy:
         print("_useastropy = True ?")
         sky = wcs.wcs_pix2world(pixcrd, 1)  
      else:
         print("_useastropy = False ?")
         sky = wcs.wcs_pix2sky(pixcrd, 1)

   except Exception as e:
      print('Problem converting to WCS: %s' % e)

   # extract the important pieces
   ra=sky[:,0]
   dec=sky[:,1]
           
   print("sky.shape = %d x %d -> ra.shape = %d" % (sky.shape[0],sky.shape[1],ra.shape[0]))   

   # and make them back into arrays
   RA=ra.reshape(X.shape)
   Dec=dec.reshape(Y.shape)

   print("RA.shape = %d x %d" % (RA.shape[0],RA.shape[1]))
   print("Dec.shape = %d x %d" % (Dec.shape[0],Dec.shape[1]))

   xc = int( center_x )
   yc = int( center_y )
   print("center = (%d,%d) , (%d,%d)" % (center_x,center_y,xc,yc))
   
   ra_xc = RA[xc,yc]
   if ra_xc < 0 :
      ra_xc = ra_xc + 360.0
   dec_xc = Dec[xc,yc]

   c = SkyCoord(ra=ra_xc*u.degree, dec=dec_xc*u.degree, frame='icrs')
   dec_dms=c.to_string('dms')
   radec_str=c.to_string('hmsdms')

   print("RADEC of (%d,%d) = (%.4f,%.4f) = %s" % (xc,yc,ra_xc,dec_xc,radec_str))

   return (RA,Dec,ra_xc,dec_xc,radius,freq_cc)
   
   
def get_gleam_sources( fitsname, min_flux=0.00, freq_cc=145 ) :
   (RA,Dec,ra_xc,dec_xc,radius,freq_cc) = find_image_gleam_sources( fitsname )
   (gleam_sources,gleam_fluxes,gleam_arcsec_dist) = find_gleam( ra_xc, dec_xc, radius*3600.00, freq_cc=freq_cc, min_flux=min_flux )
   
   return (RA,Dec,gleam_sources,gleam_fluxes,radius)   


def select_gleam_sources( fitsname ) :
   (RA,Dec,ra_xc,dec_xc,radius,freq_cc) = find_image_gleam_sources( fitsname )
   
   ra_min = RA.min()
   ra_max = RA.max()
   dec_min = Dec.min()
   dec_max = Dec.max()
   
   if ra_min < 0 :
      ra_min = ra_min + 360.00

   if ra_max < 0 :
      ra_max = ra_max + 360.00

   print("Window = (%.4f,%.4f) - (%.4f,%.4f)" % (ra_min,ra_max,dec_min,dec_max))   
   (gleam_sources,gleam_fluxes) = select_gleam( ra_min, ra_max, dec_min, dec_max, freq_cc=145 )

   return (RA,Dec,gleam_sources,gleam_fluxes,radius) 

def find_max( data, xc, yc, radius=5 ) :

   x_size = data.shape[0]
   y_size = data.shape[1]

   max_val = -1e20
   for y in range( yc-radius, yc+radius+1 ) :
      for x in range( xc-radius, xc+radius+1 ) :
         dist = math.sqrt( (x-xc)*(x-xc) + (y-yc)*(y-yc) )
        
         if x>=0 and y>=0 and x<x_size and y<y_size and dist<radius:
            if data[x,y] > max_val :
               max_val = data[x,y]
               
   return max_val

def gleam2reg_base( fitsname, RA, Dec, gleam_sources, gleam_fluxes, radius, regfile=None ) :
   if len(gleam_sources) > 0 :   
      fits = pyfits.open(fitsname)
      ext=0
      h=fits[ext].header
      wcs=pywcs.WCS(h)
      
      data = None
      if fits[0].data.ndim >= 4 :
         data = fits[0].data[0,0]
      else :
         data = fits[0].data
         
      x_size = data.shape[0]
      y_size = data.shape[1]         
               
      image_rms = data.std()   
      print("Image rms = %.4f [Jy]" % (image_rms))
      
      if regfile is None :
         regfile = fitsname.replace('.fits', '.reg')
  
      out_regfile=open(regfile,"w")          
      i=0
      
      sum=0
      sum2=0
      count=0
      for gleam_source in gleam_sources :
         flux = gleam_fluxes[i]
         # gleam_source.ra.value
                  
         # EXAMPLE : http://docs.astropy.org/en/stable/api/astropy.wcs.WCS.html         
         if _useastropy:
            print("_useastropy = True ? , checking (radec) = %s" % (gleam_source))
            # radec = np.array([gleam_source.ra.value,gleam_source.dec.value])
            # xy = wcs.wcs_world2pix(gleam_source, 1)  
            (x, y) = wcs.all_world2pix(gleam_source.ra.value,gleam_source.dec.value , 1)            
            
            image_flux = find_max( data, int(y), int(x), radius=10 )
            
            ratio = -1000
            if image_flux > -1000 :
                ratio = flux / image_flux
            
            line = "circle %d %d %d # (RA,DEC) = (%.8f,%.8f) [deg] , GLEAM_flux = %.4f [Jy] , IMAGE_flux = %.4f -> ratio = %.4f\n" % (x,y,int(flux*10),gleam_source.ra.value,gleam_source.dec.value,flux,image_flux,ratio)
                        
            if image_flux > 3*image_rms and x>=0 and y>=0 and x<x_size and y<y_size and flux>1.00 : # GLEAM_flux > 1 Jy 
               print("Source at (%d,%d) IMAGE_flux = %.4f Jy , GLEAM_flux = %.4f Jy (ra,dec) = (%.3f,%.3f) [deg] used for ratio GLEAM/IMAGE flux calculation" % (x,y,image_flux,flux,gleam_source.ra.value,gleam_source.dec.value))
               r = (flux/image_flux)
               sum = sum + r
               sum2 = sum2 + r*r
               count = count + 1
            
            out_regfile.write( line )
         else:
            print("ERROR : _useastropy=False cannot convert from (RA,DEC) -> (x,y)")
         
         i = i + 1 
      
      out_regfile.close()
      
      if count > 0 :         
         mean = sum/count
         print("DEBUG : sum=%.4f , count=%d, mean=%.4f, sum2=%.4f" % (sum,count,mean,sum2))
         rms = math.sqrt( (sum2/count) - mean*mean )
         print("Ratio GLEAM_flux / IMAGE_flux based on GLEAM %d sources = MEAN +/- RMS = %.4f +/- %.4f" % (count,mean,rms))
         print("Calibrated flux / noise / RMS = IMAGE flux / noise / rms * %.4f ( +/- %.4f)" % (mean,rms))
      else :
         print("ERROR : no GLEAM sources found for this image (count=0)")


def gleam2reg( fitsname, regfile=None ) :
   (RA,Dec,gleam_sources,gleam_fluxes,radius) = select_gleam_sources( fitsname )

   return gleam2reg_base( fitsname, RA, Dec, gleam_sources, gleam_fluxes, radius, regfile=regfile )
   
def read_text_file( filename ) :
   sources=[]

   if os.path.exists(filename) and os.stat(filename).st_size > 0 :
      file=open(filename,'r')
      data=file.readlines()
      for line in data :
         words = line.split(' ')
         if line[0] == '#' :
            continue
         
         if line[0] != "#" :
            x=float(words[0+0])
            y=float(words[1+0])
            ra=float(words[2+0])
            dec=float(words[3+0])
            peak_flux=float(words[4+0])
         
            sources.append( ImageSource(x,y,ra,dec,peak_flux) )
      file.close()
      
   else :
      print("WARNING : empty or non-existing file %s" % (filename))      

   
   return sources

def calibrate_image( fitsname, sources_list_file=None, out_fitsfile="calib_xy.fits", min_flux=0.00, use_max_peak_flux=True , freq_cc=145) :
   sum_ratio=0
   sum2_ratio=0
   found=0
   if sources_list_file is not None and os.path.exists(sources_list_file) and os.stat(sources_list_file).st_size > 0 :
      image_sources = read_text_file( sources_list_file )            
      print("Read %d sources from text file %s" % (len(image_sources),sources_list_file))
      
      if use_max_peak_flux : 
         print("calibrate_image : updating sources fluxes with maximum value around the center (from text file %s)" % (sources_list_file))
         # updates AEGEAN fluxes to maximum flux value around position (not sure if this is actually ok - possibly a temporary solution) :
         update_fluxes( fitsname, image_sources )
      else :
         print("calibrate_image : using peak flux as given in the text file %s" % (sources_list_file))
      
      if len(image_sources) > 0 :
         (RA,Dec,gleam_sources,gleam_fluxes,radius) = get_gleam_sources( fitsname, min_flux=min_flux, freq_cc=freq_cc )
         print("There should be %d GLEAM sources brighter than %.2f [Jy/beam] in the image" % (len(gleam_sources),min_flux))
         
         for image_source in image_sources :
            (gleam_source,gleam_flux,gleam_dist_arcsec) = find_source(gleam_sources,gleam_fluxes,image_source.ra,image_source.dec) 
            if gleam_source is not None :
               print("Source at (x,y) = (%d,%d) , (ra,dec) = (%.4f,%.4f) [deg], flux = %.2f [Jy/beam] corresponds to GLEAM source (%.4f,%.4f) [deg] and flux = %.2f [Jy/beam] in distance = %.2f [arcsec]" % (image_source.x,image_source.y,image_source.ra,image_source.dec,image_source.peak_flux,gleam_source.ra.value,gleam_source.dec.value,gleam_flux,gleam_dist_arcsec))
               ratio = gleam_flux/image_source.peak_flux
               sum_ratio = sum_ratio + ratio
               sum2_ratio = sum2_ratio + ratio*ratio
               found = found + 1 
            else :
               print("WARNING : source at (x,y) = (%d,%d) , (ra,dec) = (%.4f,%.4f) [deg] of flux = %.2f [Jy/beam] cannot be found in the image %s" % (image_source.x,image_source.y,image_source.ra,image_source.dec,image_source.peak_flux,fitsname))
               
         mean_ratio = (sum_ratio/found)      
         rms_ratio=math.sqrt(sum2_ratio/found - mean_ratio*mean_ratio)
         print("Mean ratio = %.4f +/- %.4f (rms) - based on %d sources" % (mean_ratio,rms_ratio,found))
         
         return (RA,Dec,gleam_sources,gleam_fluxes,radius)
   else :
      print("WARNING : no source list file name provided or file %s is empty" % (sources_list_file))
      print("Current version requires list of image sources in the following format:")
      print("X  Y RA[deg] DEC[deg] PeakFlux [Jy/beam]")
      print("It can be output of AEGEAN script (check_leakages_aegean.sh avg_I_without.fits 1 5 1000) or text file engineered manually")


   return (None,None,None,None,None)
   
def cross_match_file( filename ):
   file=open( filename , 'r' )
   # reads the entire file into a list of strings variable data :
   data=file.readlines()
   
   # Source Name, RA J2000, Dec J2000, a (arcmin), b (arcmid), PosAng, Signif_Avg, Grade
   # 4FGL J0003.3+2511 , 0.8323, 25.1912, 6.126, 5.406, 63.58, 5.415, A
   source_name = []
   source_ra   = []
   source_dec  = []
   source_err_a = []
   source_err_b = []
   source_posang = []
   source_signif_avg = []
   source_grade = []
   
   for line in data : 
      words = line.split(' ')
      if line[0] == '#' :
         continue

      if line[0] != "#" :
#         print "line = %s" % (line)         
         name1 = words[0+0]
         name2 = words[1+0]
         name = name1 + " " + name2
 
         try :
            ra  = float( words[2+0] )
            dec = float( words[3+0] )
            err_a = float( words[4+0] )
            err_b = float( words[5+0] )
            posang = float( words[6+0] )
            signif_avg = float( words[7+0] )
            grade = words[8+0]
         except :
            print("Exception : %s" % (words[2+0]))
         
         source_name.append( name )
         source_ra.append( ra )
         source_dec.append( dec )
         source_err_a.append( err_a )
         source_err_b.append( err_b )
         source_posang.append( posang )
         source_signif_avg.append( signif_avg )
         source_grade.append( grade )
         
         radius_arcsec = max( err_a , err_b ) * 60.00
         
          
         # def find_gleam( ra, dec, radius_arcsec=60, freq_cc=145, min_flux=0.00 ) :
         (out_sc,out_fluxes,out_distances_arcsec) = find_gleam( ra, dec, radius_arcsec=radius_arcsec )
         print("%s %s (%.4f,%.4f) -> found %d GLEAM sources (%s) :" % (name,grade,ra,dec,len(out_sc),(len(out_sc)>0)))
         if len(out_sc) > 0 :
            for i in range(0,len(out_sc)) :
               print("\t\t(RA,DEC) = ( %.4f , %.4f ) [deg], %.4f Jy in distance %.2f [arcmin]" % (out_sc[i].ra.value,out_sc[i].dec.value,out_fluxes[i],out_distances_arcsec[i]/60.00))
               
         print()
         print()       
         

   
   
      
   
def parse_options():
   usage="Usage: %prog [options]\n"
   usage+='\tReads FITS image and fits GLEAM sources expected to be in this image, than compares with a list of sources passed in the text file to find flux calibration ratio\n'
   parser = OptionParser(usage=usage,version=1.00)
   parser.add_option('-f','--fits','--image','--fitsfile',dest="fitsfile",default="avg_I_without.fits", help="Fits image file to calibrate with GLEAM",metavar="STRING")
   parser.add_option('-r','--regfile',dest="regfile",default="avg_I_without.reg", help="Reg file to save GLEAM sources to [default %default]",metavar="STRING")
   parser.add_option('-l','--sources','--image_sources',dest="sources_file",default="avg_I_without.txt", help="Text file with list of source for calibration, format |X  Y  RA[deg]  DEC[deg]  PeakFlux[Jy/beam]|", metavar="STRING")
   parser.add_option('--use_max_flux','--use_max_peak_flux','--max_flux',dest="use_max_peak_flux",action="store_true",default=True, help="Use maximum flux value around the source center [default %]")
   parser.add_option('--use_txt_file_flux',dest="use_max_peak_flux",action="store_false",help="Use flux values as in the text file [default %]")

   parser.add_option('--min_gleam_flux',dest="min_gleam_flux",default=0.00,help="Only use sources brighter than this limit in Jy [default %default Jy]",type="float")
#   parser.add_option('-p','--pol',dest="selected_pol",default="X", help="Selected polarisation",metavar="STRING")
#   parser.add_option('-f','--freq',dest="freq",default=230, help="Frequency in MHz",metavar="FLOAT",type="float")
#   parser.add_option('-d','--debug',action="store_true",dest="debug",default=False, help="Debug mode")
#   parser.add_option('-v','--view',action="store_true",dest="view_only",default=False, help="View only (no saving)")
   parser.add_option('-g','--gleam2sql',action="store_true",dest="gleam2sql",default=False, help="Convert GLEAM to SQL [default %s]")
   parser.add_option('-c','--freq_cc','--freq_channel','--frequency_channel',dest="freq_cc",default=145, help="Frequency channel [default %d]",type="int")
   parser.add_option('--cross_match_file', dest="cross_match_file", default=None, help="File with list of sources to cross-match with GLEAM")
   (options, args) = parser.parse_args()

   return (options, args)
   
      

if __name__ == '__main__':
   (options, args) = parse_options()     
   
   print("#################################################################")
   print("PARAMETERS :")
   print("#################################################################")
   print("Fits file = %s" % (options.fitsfile))
   print("Text file = %s" % (options.sources_file))
   print("Reg  file = %s" % (options.regfile))
   print("use_max_peak_flux = %s" % (options.use_max_peak_flux))
   print("min_gleam_flux = %.4f [Jy]" % (options.min_gleam_flux))
   print("Convert GLEAM to SQL = %s" % (options.gleam2sql))
   print("Frequency channel = %d" % (options.freq_cc))
   print("cross_match_file = %s" % (options.cross_match_file))
   print("#################################################################")

   if options.cross_match_file is not None :
      cross_match_file( options.cross_match_file )
      os.sys.exit(0)

   if options.gleam2sql :
       print("Converting GLEAM to SQL :")
       gleam2sql()
   else :
       print("calibrate_image(\"%s\",\"%s\")" % (options.fitsfile,options.sources_file))
       (RA,Dec,gleam_sources,gleam_fluxes,radius) = calibrate_image(options.fitsfile,options.sources_file,use_max_peak_flux=options.use_max_peak_flux, min_flux=options.min_gleam_flux, freq_cc=options.freq_cc)

       if gleam_sources is None or len(gleam_sources) < 0 :
          (RA,Dec,gleam_sources,gleam_fluxes,radius) = get_gleam_sources( options.fitsfile, min_flux=options.min_gleam_flux )
       else :
          print("WARNING : no gleam sources from calibrate_image - probably due to empty input source list file %s" % (options.sources_file))

       print("Saving reg file to %s" % (options.regfile))
       gleam2reg_base( options.fitsfile, RA, Dec, gleam_sources, gleam_fluxes, radius, regfile=options.regfile ) 
        