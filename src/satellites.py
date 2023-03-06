#!/usr/bin/python

# A module for known sources
# Marcin Sokolowski, July 2020

import math
import ephem

global_sky_sources = None
global_sun_index   = 0

class Satellite:
    def __init__(self, name, ra_degs, dec_degs, azim_deg=0.00, elev_deg=0.00, ut_dtm="", is_geostat=0, uxtime=0, file=None, snr=None, flux=0.00 ) :
        """Constructor requiring name, ra(degs), dec(degs), PFB coarse chan(s), dwell time (s)"""
        self.ra_degs = ra_degs
        self.dec_degs = dec_degs
        self.name = name
        self.is_geostat = is_geostat
        self.flux = flux
        self.azim_deg = azim_deg
        self.elev_deg = elev_deg
        self.uxtime   = uxtime
        self.file     = file
        self.snr      = snr

