#!/usr/bin/env python3
import sys
import os

filedir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, filedir)

from empathic import app as application
application.secret_key = 'my key'
