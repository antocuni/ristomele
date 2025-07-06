#!/bin/bash

cd ~/ristomele/

qterminal -e bash -c "cd ~/ristomele && ~/.pyenv/versions/venv/bin/uwsgi --ini uwsgi-croce-verde.ini; echo; echo SERVER IN FUNZIONE; echo Press ENTER to quit; read"
