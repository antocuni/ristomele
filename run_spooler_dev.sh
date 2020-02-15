#!/bin/bash

# run the spooler server for local dev
python -m server.spooler /tmp/spooldir -p /dev/tty --pdf
