#!/usr/bin/python

# A module for known sources
# Randall Wayth. April 2011, July 2012.

# NOTE: dwell times should preferably be multiples of 8 seconds

import math
import ephem
import time
from datetime import date, datetime

# options :
from optparse import OptionParser,OptionGroup
import sys


global_sky_sources = None
global_sun_index   = 0
global_uxtime      = None

class Source:
    def __init__( self,name,ra,dec,flux=0.00,rms=1.00,bkg=0.00, x=-1,y=-1, azim_deg=0.00, elev_deg=0.00, uxtime=0, file=None, snr=None, cat_source_index=-1, cat_source_dist_arcsec=-1,
                  freqs=['95','121','145'],dwelltime_sec=112,el_limit=40.0,known=False,gain=None,iscal=False,sources_per_image=0, 
                  min_val=None, max_val=None ):
        """Constructor requiring name, ra(degs), dec(degs), PFB coarse chan(s), dwell time (s)"""
        self.ra_degs = ra
        self.dec_degs = dec
        self.name = name
        self.freqs = freqs
        self.dwelltime_sec = dwelltime_sec
        self.el_limit = el_limit
        self.gain = gain
        self.known = known
        self.iscal = iscal
        self.x = x
        self.y = y
        self.flux = flux
        self.rms  = rms
        self.bkg  = bkg
        self.cat_source_index = cat_source_index
        self.cat_source_dist_arcsec = cat_source_dist_arcsec
        self.azim_deg = azim_deg
        self.elev_deg = elev_deg
        self.uxtime   = uxtime
        self.file     = file
        self.snr      = snr
        self.sources_per_image = sources_per_image
        
        self.min_val = min_val
        self.max_val = max_val

# based on Vincenty formula. See: http://en.wikipedia.org/wiki/Great-circle_distance
    def AngularSep(self ,ra_degs,dec_degs):
        """calc the angular distance between the source and an ra/dec location"""
        d2r = math.pi/180.0
        # compute sines and cosines of start "s" and finish "f" positions.
        slat_s = math.sin(self.dec_degs*d2r)
        slat_f = math.sin(dec_degs*d2r)
        clat_s = math.cos(self.dec_degs*d2r)
        clat_f = math.cos(dec_degs*d2r)
        dlon = self.ra_degs - ra_degs
        cdlon = math.cos(dlon*d2r)
        sdlon = math.sin(dlon*d2r)
        numerator_p1 = clat_f*sdlon
        numerator_p2 = clat_s*slat_f - slat_s*clat_f*cdlon
        numerator = math.sqrt(numerator_p1*numerator_p1 + numerator_p2*numerator_p2)
        denom = slat_s*slat_f + clat_s*clat_f*cdlon
        return math.atan2(numerator,denom)

    def __repr__(self):
        return "< "+self.name+": RA(degs): "+str(self.ra_degs)+". DEC: "+str(self.dec_degs)+". Freqs: "+str(self.freqs)+". El_limit: "+str(self.el_limit)+" degs >"
    

def LoadSources( uxtime=None ):
  if uxtime is None :
     uxtime = time.time()
  
  dtm = datetime.utcfromtimestamp( uxtime )
  ephem_dtm = ephem.Date( dtm )

  sun = ephem.Sun()
  sun.compute( ephem_dtm )
  print("DEBUG (skysources) : Sun position is (RA,DEC) = (%.4f,%.4f) [deg]" % (sun.ra*(180.0/math.pi),sun.dec*(180.0/math.pi)))
  
  allsrcs = []
  # sun pos when the script is run
  s = Source('Sun',sun.ra*180.0/math.pi,sun.dec*180.0/math.pi,freqs=['62;63;69;70;76;77;84;85;93;94;103;104;113;114;125;126;139;140;153;154;169;170;187;188'],known=True,dwelltime_sec=296,gain=14,el_limit=30)
  allsrcs.append(s)
#  s = Source('SCP',0.0,-89.9,known=True,dwelltime_sec=296,gain=0,el_limit=20)
#  allsrcs.append(s)
#  s = Source('EoR0',0.0,-30.0)
#  allsrcs.append(s)
  s = Source('3C33',17.2202442,13.3372789,known=True)
  allsrcs.append(s)
  s = Source('PKS0131-36',23.490583,-36.493250)
  allsrcs.append(s)
  s = Source('ForA',50.673825,-37.208227,known=True)
  allsrcs.append(s)
  s = Source('3C098',59.7268408,10.4341758)
  allsrcs.append(s)
  s = Source('PKS0349-27',57.899000,-27.742972) # Gianni's polarised source
  allsrcs.append(s)
#  s = Source('EoR1',60.0,-27.0)
#  allsrcs.append(s)
  s = Source('PKS0408-65',62.0849171,-65.7525217,iscal=True,known=True)
  allsrcs.append(s)
  s = Source('PKS0410-75',62.2020517,-75.1220352)
  allsrcs.append(s)
  s = Source('J0437-4715',69.3162,-47.2525)
  allsrcs.append(s)
  s = Source('PKS0442-28',71.157083,-28.165139)
  allsrcs.append(s)
  s = Source('PicA',79.9571708,-45.7788278,iscal=True,known=True)
  allsrcs.append(s)
  s = Source('LMC',80.8939,-69.7561,dwelltime_sec=240)
  allsrcs.append(s)
  s = Source('SMC',13.1583333,-72.800278,dwelltime_sec=240)
  allsrcs.append(s)
  s = Source('Crab',83.633212,22.01446,iscal=True,known=True,el_limit=35)
  allsrcs.append(s)
  s = Source('M42',83.8186621,-5.3896789,known=True)
  allsrcs.append(s)
  s = Source('A3376',90.0,-40.0, freqs=['69','93','117','141','165'])
  allsrcs.append(s)
  s = Source('3C161',96.7921548,-5.8847717)
  allsrcs.append(s)
  s = Source('Bullet',105.0,-56.0,freqs=['69','93','117','141','165'])
  allsrcs.append(s)
  s = Source('PupA',126.0307,-42.9963,known=True)
  allsrcs.append(s)
  s = Source('HydA',139.5236198,-12.0955426,iscal=True,known=True)
  allsrcs.append(s)
  s = Source('TN0924',141.0,-19.0,freqs=['175'])
  allsrcs.append(s)
  s = Source('3C227',146.9381792,7.4223178)
  allsrcs.append(s)
  s = Source('EoR2',170.0,-10.0)
  allsrcs.append(s)
  s = Source('VirA',187.7059304, 12.3911231,iscal=True,known=True)
  allsrcs.append(s)
  s = Source('3C278',193.65083,-12.56306)   # this is close to VirA
  allsrcs.append(s)
  s = Source('3C283',197.9171042,-22.2845667)
  allsrcs.append(s)
  s = Source('CenA',201.3650633,-43.0191125,known=True,iscal=True)
  allsrcs.append(s)
  s = Source('3C317',229.185372,7.021626)
  allsrcs.append(s)
  s = Source('CirX1',230.17021,-57.166694, el_limit=45, dwelltime_sec=56)
  allsrcs.append(s)
  s = Source('PKS1610-60',243.7659992,-60.9071658,known=False)
  allsrcs.append(s)
  s = Source('B1642-03',251.258500, -3.299867,dwelltime_sec=240,known=False)
  allsrcs.append(s)
  s = Source('HerA',252.788,4.99278,iscal=True,known=True)
  allsrcs.append(s)
  s = Source('3C353',260.1173258,-0.9796169,known=True)
  allsrcs.append(s)
  s = Source('SgrA',266.417,-29.0078,gain=5,known=True)
  allsrcs.append(s)
  s = Source('PKS1814-63',274.8958429,-63.7633858)
  allsrcs.append(s)
  s = Source('SS433',287.95685, 4.9830, el_limit=45)
  allsrcs.append(s)
  s = Source('GRS1915',288.79813,10.945778, el_limit=45, dwelltime_sec=56)
  allsrcs.append(s)
  #s = Source('PKS1932-46',293.985649,-46.344601,iscal=True,known=True)
  s = Source('PKS1932-46',293.985649,-46.344601,known=True)
  allsrcs.append(s)
  s = Source('CygA',299.8681525,40.7339156,el_limit=20.0,known=True)
  allsrcs.append(s)
  s = Source('A3667',303.1254,-56.8165,freqs=['69','93','117','141','165'],dwelltime_sec=236)
  allsrcs.append(s)
  s = Source('3C409',303.6149855,23.5813630)
  allsrcs.append(s)
  s = Source('3C433',320.935559,25.069967)
  allsrcs.append(s)
  s = Source('3C444',333.607250,-17.026611,el_limit=30,iscal=True,known=True)
  allsrcs.append(s)
  #s = Source('PKS2153-69',329.2749187,-69.6899125,iscal=True,known=True)
  s = Source('PKS2153-69',329.2749187,-69.6899125,known=True)
  allsrcs.append(s)
  s = Source('PKS2356-61',359.768178,-60.916466,iscal=True,known=True)
  allsrcs.append(s)

  # sources from G0011
#  s = Source('J0041-09',10.4574,-9.3493,freqs=[71,121,169])
#  allsrcs.append(s)
#  s = Source('J0552-2103',88.2536,-21.0809,freqs=[71,121,169])
#  allsrcs.append(s)
#  s = Source('J0817-07',124.3463,-7.5151,freqs=[71,121,169])
#  allsrcs.append(s)
#  s = Source('J0909-0939',137.234,-9.6725,freqs=[71,121,169])
#  allsrcs.append(s)
#  s = Source('J1202-0650',180.7082,-6.849,freqs=[71,121,169])
#  allsrcs.append(s)
#  s = Source('J1215-39',183.89,-38.9929,freqs=[71,121,169])
#  allsrcs.append(s)
#  s = Source('J1258-01',194.6899,-1.7697,freqs=[71,121,169])
#  allsrcs.append(s)
#  s = Source('J1259-04',194.8641,-4.1915,freqs=[71,121,169])
#  allsrcs.append(s)
#  s = Source('J1303-24',195.9278,-24.2806,freqs=[71,121,169])
#  allsrcs.append(s)
#  s = Source('J1327-31',201.9823,-31.4983,freqs=[71,121,169])
#  allsrcs.append(s)
#  s = Source('J1347-32',206.88,-32.8496,freqs=[71,121,169])
#  allsrcs.append(s)
#  s = Source('J1358-47',209.6776,-47.8116,freqs=[71,121,169])
#  allsrcs.append(s)
#  s = Source('J1407-5100',211.9007,-51.021,freqs=[71,121,169])
#  allsrcs.append(s)
#  s = Source('J1638-64',249.5789,-64.3594,freqs=[71,121,169])
#  allsrcs.append(s)
#  s = Source('PSZ1G018.75',255.5725,-0.9984,freqs=[71,121,169])
#  allsrcs.append(s)
#  s = Source('J2012-56',303.0754,-56.8261,freqs=[71,121,169])
#  allsrcs.append(s)
#  s = Source('J2034-35',308.6712,-35.8201,freqs=[71,121,169])
#  allsrcs.append(s)
#  s = Source('J2152-19',328.0913,-19.6330,freqs=[71,121,169])
#  allsrcs.append(s)
#  s = Source('J2154-57',328.5834,-57.8575,freqs=[71,121,169])
#  allsrcs.append(s)
#  s = Source('J2201-59',329.5707,-60.4365,freqs=[71,121,169])
#  allsrcs.append(s)
#  s = Source('J2210-12',332.5536,-12.1642,freqs=[71,121,169])
#  allsrcs.append(s)
#  s = Source('J2246-52',341.5637,-52.7166,freqs=[71,121,169])
#  allsrcs.append(s)
#  s = Source('J2249-64',342.4462,-64.4186,freqs=[71,121,169])
#  allsrcs.append(s)

  # for A00001
#  s = Source('SSC',202.0,-37.0,freqs=[78,121,156])
#  allsrcs.append(s)

  # for D0000
#  allsrcs.append(Source('PKS1718',259.0,-65,freqs=[78,121,156]))

  # for D0007
#  allsrcs.append(Source('K2',172.5,1.5,freqs=[121,145],dwelltime_sec=296))
#  allsrcs.append(Source('K2_F3',335,-14.0,freqs=[121,145],dwelltime_sec=296))

  # For G0016
#  allsrcs.append(Source('WASP-18b',24.3542,-45.678,freqs=[69],dwelltime_sec=240,el_limit=30))
#  allsrcs.append(Source('HD14004b',89.9568,-48.2397,freqs=[69],dwelltime_sec=240,el_limit=30))

  
  return allsrcs

def GetGlobalSources() :
  global global_sky_sources
  global global_uxtime
  
  if global_sky_sources is None :
     print("DEBUG (skysources) : sources not initialised -> LoadSources called")
     global_sky_sources = LoadSources( global_uxtime )
     
  return global_sky_sources

def SetGlobalUnixTime( uxtime ) :
  global global_uxtime
  
  global_uxtime = uxtime

def GetKnownSources( sources=None, selection=["CenA","Sun","HydA","PicA","HerA","3C444","VirA","CygA","Crab","ForA","PupA"] ) :
  if sources is None :
     sources = GetGlobalSources()
  
  known_sources = []
  for src in sources:
    if src.known and src.name in selection : 
       known_sources.append(src)

  return known_sources



def angdist_arcsec( ra_deg, dec_deg, ra_find_deg, dec_find_deg ):
   if ra_deg == ra_find_deg and dec_deg == dec_find_deg :
       # WARNING otherwise math.acos( cos_x ) throughs and exception !!!??? Perhaps cos_x > 1 ??? a little bit ???
       return 0.00

   RAD2ARCSEC = ( ( 180.00 / math.pi )*3600. )
   
   ra_rad = (math.pi/180.00)*ra_deg
   dec_rad = (math.pi/180.00)*dec_deg
   
   ra_find_rad = (math.pi/180.00)*ra_find_deg
   dec_find_rad = (math.pi/180.00)*dec_find_deg
   
   sin_dec_find_ra = math.sin(dec_find_rad)
   cos_dec_find_ra = math.cos(dec_find_rad)

   cos_x = math.sin(dec_rad)*sin_dec_find_ra + math.cos(dec_rad)*cos_dec_find_ra*math.cos( ra_rad - ra_find_rad );
   dist_rad = math.acos( cos_x );
   dist_arcsec = dist_rad * RAD2ARCSEC
   
   return dist_arcsec


def CalSources(allsrcs):
  calsrcs = []
  for s in allsrcs:
    if s.iscal: calsrcs.append(s)
  return calsrcs

def InRA_Range(ra_hrs, ha_range_hrs, sources=None):
  if sources is None :
     sources = GetGlobalSources()

  srcs = []
  # calc ranges of RA that are OK for this source.
  ra_min = ra_hrs - ha_range_hrs
#  if ra_min < 0.0: ra_min += 24.0
  ra_max = ra_hrs + ha_range_hrs
#  if ra_max >= 24.0: ra_max -= 24.0
  for s in sources:
    src_ra_hrs = s.ra_degs*24.0/360.0
    if src_ra_hrs > ra_min and src_ra_hrs < ra_max: srcs.append(s)
  return srcs

def InBeam(sources, beam_ra_degs, beam_dec_degs,beam_radius_degs):
    srcs = []
    for s in sources:
        if s.AngularSep(beam_ra_degs, beam_dec_degs)*180/math.pi < beam_radius_degs:
            srcs.append(s)
    return srcs

def FindCal(sources, ra_degs, za_limit_rad=math.pi/4.0, lat_degs=-26.7):
    """Find the subset of sources within a ZA limit given an RA. Return list of tuples (calsrc, za)"""
    outsrcs = []
    for s in sources:
        ang_sep = s.AngularSep(ra_degs,lat_degs)
        if ang_sep < za_limit_rad:
            outsrcs.append((s,ang_sep))
    # sort the result by zenith angle
    newlist=sorted(outsrcs, key=lambda item: item[1])
    if len(newlist) > 0:
        return newlist
    else:
        return []


def GetSun( sources=None ) :
  if sources is None :
     sources = GetGlobalSources()
     
  sun = None
  if len(sources) > 0 :
     sun = sources[global_sun_index]
  
  if len(sources) <= 0 or sun is None or sun.name.lower()!="sun" :  
     print("ERROR : could not find Sun amongst the catalog sources !")
     return None
     
  return sun 


def GetSunDistanceArcsec(  ra_degs, dec_degs ) :
   sun = GetSun()
   
   if sun is not None :
      dist_arcsec = angdist_arcsec( ra_degs, dec_degs, sun.ra_degs, sun.dec_degs )
      
      return (dist_arcsec,sun)

   print("ERROR : could not find Sun amongst the catalog sources !")
   
   return (None,None)

def FindClosestSource( ra_degs, dec_degs, sources=None, radius_arcsec=1e20 , check_error=True, min_uxtime=None, max_uxtime=None ):
  if sources is None :
     sources = GetGlobalSources()

  min_dist = 1e20
  closest_source = None
  for src in sources :     
     if min_uxtime is not None :
        if src.uxtime < min_uxtime :
           continue

     if max_uxtime is not None : 
        if src.uxtime > max_uxtime :
           continue

     dist_arcsec = angdist_arcsec( ra_degs, dec_degs, src.ra_degs, src.dec_degs )
     
     if dist_arcsec < min_dist :
        min_dist = dist_arcsec
        closest_source = src

  ret = False
  if closest_source is None :
     if check_error :
        print("\t\tERROR : no closest source found !!!??? Number of sources = %d" % (len(sources)))
        return (False,None,min_dist)
  else :
     if min_dist < radius_arcsec :
         ret = True
         print("\tDEBUG : Returning source to (%.4f,%.4f) [deg] is %s at (%.4f,%.4f) distance = %.2f [arcsec]" % (ra_degs,dec_degs,closest_source.name,closest_source.ra_degs,closest_source.dec_degs,min_dist))
     else :
        print("\tDEBUG : no known source in radius %.2f [arcsec] around (%.4f,%.4f) [deg] the closest is %s at (%.4f,%.4f) distance = %.2f [arcsec]" % (radius_arcsec,ra_degs,dec_degs,closest_source.name,closest_source.ra_degs,closest_source.dec_degs,min_dist))    
  
  return (ret,closest_source,min_dist)

def FindClosestInTime( uxtime, min_uxtime=None, max_uxtime=None, sources=None ):
  if sources is None :
     sources = GetGlobalSources()

  ret = False
  min_dist = 1e20
  closest_source = None
  for src in sources :     
     if min_uxtime is not None :
        if src.uxtime < min_uxtime :
           continue

     if max_uxtime is not None : 
        if src.uxtime > max_uxtime :
           break

     dist_sec = math.fabs( src.uxtime - uxtime )
     
     if dist_sec < min_dist :
        min_dist = dist_sec
        closest_source = src
        ret = True

  
  return (ret,closest_source,min_dist)


def FindBrightestSource( ra_degs, dec_degs, sources=None, radius_arcsec=1e20 , check_error=True, min_uxtime=None, max_uxtime=None, file=None, same_image_dt=0.0001, desc="" ):
  if sources is None :
     sources = GetGlobalSources()

  brightest_dist = 1e20
  brightest_source = None
  
  uxtime = None
  if min_uxtime is not None and max_uxtime is not None :
     uxtime = min_uxtime
     uxtime = max_uxtime
  
  for src in sources :   
     if file is not None :
        if src.file != file :
           continue
           
     matched = False  
     if uxtime is not None :
        if math.fabs( uxtime - src.uxtime ) < same_image_dt :
           matched = True        

     if not matched :
        if min_uxtime is not None :
           if src.uxtime < min_uxtime :
              continue

        if max_uxtime is not None : 
           if src.uxtime > max_uxtime :
              continue

#     try : 
     dist_arcsec = 0
     if radius_arcsec is not None and radius_arcsec > 0 and radius_arcsec < (360*3600) :
        dist_arcsec = angdist_arcsec( ra_degs, dec_degs, src.ra_degs, src.dec_degs )
#     except :
#        print("ERROR : exception caught in angdist_arcsec( %.4f , %.4f , %.4f , %.4f )" % (ra_degs, dec_degs, src.ra_degs, src.dec_degs))
     
     if radius_arcsec is None or dist_arcsec < radius_arcsec :
        if brightest_source is None or src.flux > brightest_source.flux :
           brightest_dist = dist_arcsec
           brightest_source = src

  ret = False
  if brightest_source is None :
     if check_error :
        print("\t\tERROR : no brightest source found !!!??? Number of sources = %d" % (len(sources)))
        return (False,None,brightest_dist)
  else :
     if brightest_dist < radius_arcsec :
         ret = True
         print("\tDEBUG (%s) : Returning brigthest source close to (%.4f,%.4f) [deg] is %s at (%.4f,%.4f) distance = %.2f [arcsec] , flux = %.4f [Jy]" % (desc,ra_degs,dec_degs,brightest_source.name,brightest_source.ra_degs,brightest_source.dec_degs,brightest_dist,brightest_source.flux))
     else :
         if brightest_source is None :
            print("\tDEBUG(%s) : no known brigthest source in radius in file = %s" % (desc,file))
         else :
            print("\tDEBUG(%s) : no known brigthest source in radius %.2f [arcsec] around (%.4f,%.4f) [deg] the closest is %s at (%.4f,%.4f) distance = %.2f [arcsec]" % (desc,radius_arcsec,ra_degs,dec_degs,brightest_source.name,brightest_source.ra_degs,brightest_source.dec_degs,brightest_dist))    
  
  return (ret,brightest_source,brightest_dist)



def FindSourceByName( name , check_error=True, sources=None ):
   if sources is None :
       sources = GetGlobalSources()
   
   if len(sources) > 0 :
      for src in sources : 
         if src.name == name :
            return (True,src,0.00)
   else :
      if check_error :
         print("\tERROR : no sources in the list ???")


   return (False,None,1e20)

def FindClosestSourceXY( x, y, sources, radius, debug_level=0 ): # radius in pixels 

  index = 0
  min_dist = 1e20
  closest_source = None
  closest_index = -1
  for src in sources :     
     dist = math.sqrt( (x-src.x)**2 + (y-src.y)**2 )
     
     if dist < min_dist :
        min_dist = dist
        closest_source = src
        closest_index = index
     
     index += 1

  ret = False    
  if min_dist < radius :
     ret = True
     if debug_level > 0 :
        print("\tDEBUG : Returning XY-source to (%d,%d) is %s at (%d,%d) distance = %.2f [pixels]" % (x,y,closest_source.name,closest_source.x,closest_source.y,min_dist))
  else :
     if debug_level > 0 :
        if closest_source is not None :        
           print("\tDEBUG : no known XY-source in radius %.2f [pixels] around (%d,%d) the closest is %s at (%d,%d) distance = %.2f [pixels]" % (radius,x,y,closest_source.name,closest_source.x,closest_source.y,min_dist))    
        else :
           print("\tDEBUG : no source in the list yet")
  
  return (ret,closest_source,closest_index)
  


def parse_options(idx):
   usage="Usage: %prog [options]\n"
   usage+='\tskysources.py  \n'
   parser = OptionParser(usage=usage,version=1.00)
#   parser.add_option('-a','--a_team','--ateam','--a_team_sources',action="store_true",dest="check_ateam_sources", default=True, help="Check A-team sources [default %default]")
#   parser.add_option('-r','--a_team_radius','--aradius','--a_team_sources_radius',dest="a_team_sources_radius", default=3.8, help="A-team sources radius [deg] should be at least 1 beam size [default %default is
#   parser.add_option('-s','--sun_radius','--sradius','--sunradius',dest="sun_radius", default=8, help="Sun radius [deg] might even be 10 degrees [default %default is ~2 beam sizes at 150 MHz]")
   parser.add_option('-r','--ra','--ra_degs',dest="ra_degs", default=0.00, help="RA [degs] [default %default]",type="float")
   parser.add_option('-d','--dec','--dec_degs',dest="dec_degs", default=0.00, help="DEC [degs] [default %default]",type="float")
   
#   parser.add_option('-m','--mean_cc',action="store_true",dest="mean_cc",default=True, help="Mean of coarse channels [default %]")
#   parser.add_option('--no_mean_cc',action="store_false",dest="mean_cc",default=True, help="Turn off calculation of mean of coarse channels [default %]")
#   parser.add_option('-o','--outdir',dest="outdir",default=None, help="Output directory [default %]")
#   parser.add_option('--meta_fits','--metafits',dest="metafits",default=None, help="Metafits file [default %]")
   parser.add_option('--add_extension','--add_ext','--postfix','--ext',dest="add_extension",default=None, help="Add extension to values in list file [default None]")

   (options, args) = parser.parse_args(sys.argv[idx:])

   return (options, args)
 

if __name__ == "__main__":
   (options, args) = parse_options(1) 

   print("##############################################################")
   print("PARAMETERS :")
   print("##############################################################")
   print("(RA,DEC)              = ( %.4f , %.4f ) [deg]" % (options.ra_degs,options.dec_degs))
   print("##############################################################")
   
   (ret,src,min_dist_arcsec) = FindClosestSource( options.ra_degs , options.dec_degs )
   if ret :
      print("Found %s source close to (RA,DEC) = (%.4f,%.4f) [deg] in distance of %.2f [arcsec]" % (src.name, options.ra_degs , options.dec_degs, min_dist_arcsec))
   else :
      print("No source found around  (RA,DEC) = (%.4f,%.4f) [deg]" % (options.ra_degs , options.dec_degs))



#  allsrcs = LoadSources()
#  calsrcs = CalSources(allsrcs)
#  print("There are "+str(len(allsrcs))+" sources.")
#  print("There are "+str(len(calsrcs))+" cal sources.")
#  #for s in calsrcs: print s.name
#  for lst in range(24):
#    cals_this_lst = FindCal(calsrcs,lst*15.0)
#    print("Cal sources at LST "+str(lst))
#    for s,za in cals_this_lst:
#        print("%s ZA: %.1f" % ( s,za*180.0/math.pi))

