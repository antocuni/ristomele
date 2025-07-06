#!/bin/bash

cd ~/ristomele/mobile

# the maximum size seems to be 1100x700, more than that I get
#    pygame.error: OpenGL error: 00000502


qterminal -e bash -c "~/.pyenv/versions/venv/bin/python launcher/main.py --remote --size=1100x700 --fake-fullscreen; echo; echo Press ENTER to quit; read"
