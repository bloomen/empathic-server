#!/usr/bin/env python3
import logging
import sys
logging.basicConfig(stream=sys.stderr)
sys.path.insert(0, '/home/pi/workspace/empathic-server/empathic')
from empathic import app as application
application.secret_key = 'my key'
