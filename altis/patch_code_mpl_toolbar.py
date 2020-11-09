#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------
#
# Matplotlib toolbar doesn't provide 'home', 'back' or 'forward' button event
#
# Subclass a matplotlib backend : "monkey-patched approach"
# https://stackoverflow.com/questions/14896580/matplotlib-hooking-in-to-home-back-forward-button-events
#
# Created by Fabien Blarel on 2019-04-19.
# CeCILL Licence 2019 CTOH-LEGOS.
# ----------------------------------------------------------------------
import matplotlib.pyplot as plt
from matplotlib.backend_bases import NavigationToolbar2

home = NavigationToolbar2.home

def new_home(self, *args, **kwargs):
    print ('new home')
    NavigationToolbar2.mode='home'
    home(self, *args, **kwargs)

NavigationToolbar2.home = new_home

back = NavigationToolbar2.back

def new_back(self, *args, **kwargs):
    print ('new back')
    back(self, *args, **kwargs)

NavigationToolbar2.back = new_back

forward = NavigationToolbar2.forward

def new_forward(self, *args, **kwargs):
    print ('new forward')
    forward(self, *args, **kwargs)

NavigationToolbar2.forward = new_forward

zoom = NavigationToolbar2.zoom

def new_zoom(self, *args, **kwargs):
    print ('new zoom')
    zoom(self, *args, **kwargs)

NavigationToolbar2.zoom = new_zoom

#fig = plt.figure()
#plt.text(0.35, 0.5, 'Hello world!', dict(size=30))
#plt.show()

