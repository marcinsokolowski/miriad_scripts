import math
import sys

from optparse import OptionParser,OptionGroup
import errno
import getopt
import optparse

from datetime import datetime
import time
from astropy.time import Time


def parse_options(idx):
   parser=optparse.OptionParser()
   parser.set_usage("""sat_probability.py""")
   parser.add_option("--coinc_radius","--radius",dest="coinc_radius",default=4.00,help="Coincidence radius [deg] [default: %default]",type="float")
   parser.add_option("--min_elev","--min_elevation",dest="min_elevation",default=25,help="Minimum elevation [default: %default]",type="float")
   parser.add_option("--transients","--n_transients",dest="n_transients",default=1,help="Number of transients [default: %default]",type="int")
   parser.add_option("--satellites","--n_satellites","--n_sat",dest="n_satellites",default=1,help="Number of satellites [default: %default]",type="int")
   
   (options,args)=parser.parse_args(sys.argv[idx:])

   return (options, args)



def matching_probability( coinc_radius_deg = 4.00 , min_elev = 25 , n_transients = 1 , n_satellites = 1 ) :
   coinc_radius_rad = (math.pi/180.00)*coinc_radius_deg
   min_elev_rad = min_elev * (math.pi/180.00)
#   prob =  pow( math.sin( coinc_radius_rad / 2 ) , 2 ) / pow( math.sin( (math.pi/2 - min_elev_rad) / 2 ) , 2 )
   prob =  pow( ( math.sin( coinc_radius_rad / 2 ) / math.sin( (math.pi/2 - min_elev_rad) / 2 ) ) , 2 )
   
   prob_t = prob * n_transients
   
   print("Probability of matching single transient = %.4f" % (prob))
   print("Probability of matching %d transients = %.4f" % (n_transients,prob_t))

   # Bernouli :
   p_s = prob * n_satellites
   if p_s > 1 :
      print("WARNING : large number of satellites -> %d * %.4f = %.4f > 1 !!!" % (n_satellites,prob,p_s))
      p_s = 1.00
   e_match = n_transients * p_s 
   sigma_match = math.sqrt( e_match * ( 1 - p_s ) )   
   
   print("Expected number of random matches = %.4f +/- %.4f\n" % (e_match,sigma_match))

if __name__ == '__main__':
#    n_transients = 1 
#    if len(sys.argv) > 1:
#       n_transients = int( sys.argv[1] )

    (options, args) = parse_options( 0 )
       
    matching_probability( coinc_radius_deg=options.coinc_radius, min_elev=options.min_elevation, n_transients=options.n_transients, n_satellites=options.n_satellites )
       

  
