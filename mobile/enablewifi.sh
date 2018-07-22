IP=`adb shell ifconfig wlan0 | grep 'inet addr:' | cut -d: -f2 | awk '{ print $1}'`
echo $IP

echo IP: $IP
adb tcpip 5555
sleep 1
adb connect $IP:5555
