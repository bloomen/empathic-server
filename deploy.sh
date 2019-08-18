#!/bin/bash
set -x
ssh pi@192.168.1.7 'cd ~/workspace/empathic-server && git pull'
ssh pi@192.168.1.7 'sudo systemctl reload apache2'
