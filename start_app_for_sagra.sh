#!/bin/bash

cd ~/ristomele/mobile

# the maximum size seems to be 1100x700, more than that I get
#    pygame.error: OpenGL error: 00000502


gnome-terminal -- /home/sagra/.virtualenvs/ristomele/bin/python launcher/main.py --remote --size=1100x700 --fake-fullscreen
read
