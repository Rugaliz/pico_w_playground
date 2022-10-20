import network
import socket
import time
import urequests
from machine import Pin
import uasyncio as asyncio
import ujson

sensor_temp = machine.ADC(4)
conversion_factor = 3.3 / (65535)

led = Pin(15, Pin.OUT)
onboard = Pin("LED", Pin.OUT, value=0)

ssid = ''
password = ''

html = """<!DOCTYPE html>
<html>
 <head> <title>Pico W</title> </head>
 <body> <h1>Pico W</h1>
 <p>%s</p>
 </body>
</html>
"""

wlan = network.WLAN(network.STA_IF)
def connect_to_network():
    wlan.active(True)
    wlan.config(pm = 0xa11140)
    wlan.ifconfig(('192.168.1.99', '255.255.255.0', '192.168.1.1', '8.8.8.8'))
    # Disable power-save mode
    wlan.connect(ssid, password)
    max_wait = 10
    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        max_wait -= 1
        print('waiting for connection...')
        time.sleep(1)
    if wlan.status() != 3:
        raise RuntimeError('network connection failed')
    else:
         print('connected')
         status = wlan.ifconfig()
         print('ip = ' + status[0])

def read_temperature():
        reading = sensor_temp.read_u16() * conversion_factor
        # The temperature sensor measures the Vbe voltage of a biased bipolar diode, connected to the fifth ADC channel
        # Typically, Vbe = 0.706V at 27 degrees C, with a slope of -1.721mV (0.001721) per degree.
        temperature = 27 - (reading - 0.706)/0.001721
        return round(temperature, 2)

async def serve_client(reader, writer):
    global html
    print("Client connected")
    request_line = await reader.readline()
    print("Request:", request_line)
    # We are not interested in HTTP request headers, skip them
    while await reader.readline() != b"\r\n":
        pass
    request = str(request_line)
    led_on = request.find('/light/on')
    led_off = request.find('/light/off')
    temp_querry = request.find('/temperature')
    data_request = request.find('/jsondata')  # request for json data
    print( 'led on = ' + str(led_on))
    print( 'led off = ' + str(led_off))
    
    stateis = ""
    json_payload = False
    if led_on == 6:
        print("led on")
        led.value(1)
        stateis = "LED is ON"
    
    if led_off == 6:
        print("led off")
        led.value(0)
        stateis = "LED is OFF"
        
    if temp_querry == 6:
        temperature = read_temperature()
        stateis = f"Internal temperature: {temperature} C\370"
    
    if data_request == 6:
        temperature = read_temperature()
        data = {
            "pico_chip_temp": temperature,
            }
        data_json = ujson.dumps(data)
        json_payload = True
    
    if json_payload:
        print("Will send json data")
        response = data_json
        writer.write('HTTP/1.0 200 OK\r\nContent-type: application/json\r\n\r\n')
        writer.write(response)
        json_payload = False
        
    else:
        response = html % stateis
        writer.write('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
        writer.write(response)


    await writer.drain()
    await writer.wait_closed()
    print("Client disconnected")

async def main():
    print('Connecting to Network...')
    connect_to_network()
    print('Setting up webserver...')
    asyncio.create_task(asyncio.start_server(serve_client, "0.0.0.0", 80))
    print('Webserver started')
    while True:
        onboard.on()
        #print("heartbeat")
        await asyncio.sleep(0.5)
        onboard.off()
        await asyncio.sleep(5)

try:
    asyncio.run(main())
finally:
    asyncio.new_event_loop()

