sudo cp *.service /etc/systemd/system/

# now in theory we could do "systemctl enable ristomele", to automatically
# start at at boot, but it doesn't work. Instead, we do it manually

sudo ln -fs /etc/systemd/system/ristomele*.service /etc/systemd/system/multi-user.target.wants/

sudo systemctl daemon-reload

# install stunnel config for HTTPS on port 443
# stunnel4 on Debian is disabled by default; set ENABLED=1 so the service starts
sudo sed -i 's/^ENABLED=0/ENABLED=1/' /etc/default/stunnel4
sudo cp ../stunnel.conf /etc/stunnel/ristomele.conf
sudo systemctl enable stunnel4
sudo systemctl restart stunnel4
