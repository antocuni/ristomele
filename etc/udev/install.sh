# To find the attributes:
# udevadm info -a  -p $(udevadm info -q path -n /dev/usb/lp0)

sudo cp 99-my-printer.rules /etc/udev/rules.d/
sudo udevadm control -R # reload the rules
