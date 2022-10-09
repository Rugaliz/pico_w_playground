import network   # handles connecting to WiFi
import urequests # handles making and servicing network requests
import machine
import rp2
from time import sleep
import socket
led = machine.Pin("LED", machine.Pin.OUT)
led.on()
sleep(1)
led.off()
# Connect to network
rp2.country('PT')
wlan = network.WLAN(network.STA_IF)
wlan.active(True)

# Fill in your network name (ssid) and password here:
ssid = 'RugalizCyberconnect'
password = ''
wlan.connect(ssid, password)


 # Wait for connect or fail
max_wait = 10
while max_wait > 0:
    if wlan.status() < 0 or wlan.status() >= 3:
        break
    max_wait -= 1
    print('waiting for connection...')
    sleep(1)
# Handle connection error
if wlan.status() != 3:
    raise RuntimeError('network connection failed')
else:
    print('connected')
    status = wlan.ifconfig()
    print( 'ip = ' + status[0] )
print(wlan.config('channel'))
print(wlan.config('essid'))
print(wlan.config('txpower'))

# Open socket
addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
s = socket.socket()
s.bind(addr)
s.listen(1)
print('listening on', addr)


# 
html = """<!DOCTYPE html>
<html>
    <head> <title>Pico W</title> </head>
    <body> <h1>Pico W</h1>
        <p>Hello World</p>
        <p>Hello World</p>
    </body>
</html>
"""
# Listen for connections
while True:
    try:
        cl, addr = s.accept()
        print('client connected from', addr)
        cl_file = cl.makefile('rwb', 0)
        while True:
            line = cl_file.readline()
            if not line or line == b'\r\n':
                break
        response = html
        cl.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
        cl.send(response)
        cl.close()
    except OSError as e:
        print(e)
        cl.close()
        print('connection closed')
