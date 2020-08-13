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
# CeCILL Licence 2019 CTOH-LEGOS.
# ----------------------------------------------------------------------

class Singleton(object):
    """
        Singleton class
    """
    def __new__(cls):
        """
            __new__ method
        """
        if not hasattr(cls, 'instance'):
            cls.instance = super(Singleton, cls).__new__(cls)
        return cls.instance
