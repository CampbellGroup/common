# -*- coding: utf-8 -*-
"""
Created on Sun Dec 25 23:06:15 2016

@author: scientist

This file makes GUI compatible with both PyQt4 and PyQt5.
"""
try:
    from PyQt5 import QtGui, QtCore, uic
except ImportError:
    from PyQt4 import QtGui, QtCore, uic
