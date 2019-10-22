#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------
#
# DatasetSelection Class
#
# This class build a mask selection of the altimetric dataset from 
# matplotlib collection 
#
# Created by Fabien Blarel on 2019-04-19. 
# Copyright (c) 2019 Legos/CTOH. All rights reserved.
# ----------------------------------------------------------------------



class Singleton(object):
   def __new__(cls):
       if not hasattr(cls, 'instance'):
           cls.instance = super(Singleton, cls).__new__(cls)
       return cls.instance
