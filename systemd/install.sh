sudo cp *.service /etc/systemd/system/

# now in theory we could do "systemctl enable ristomele", to automatically
# start at at boot, but it doesn't work. Instead, we do it manually

sudo ln -fs /etc/systemd/system/ristomele-*.service /etc/systemd/system/multi-user.target.wants/

sudo systemctl daemon-reload
