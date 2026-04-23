import network
import time
import config

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('Connecting to network...')
        wlan.connect(config.WIFI_SSID, config.WIFI_PASS)
        
        # Wait for connection with timeout
        timeout = 10
        start_time = time.time()
        while not wlan.isconnected() and (time.time() - start_time) < timeout:
            time.sleep(1)
            print(".", end="")
            
    if wlan.isconnected():
        print('\nConnected to Wi-Fi!')
        print('Network config:', wlan.ifconfig())
    else:
        print('\nFailed to connect to Wi-Fi. Check your credentials.')

connect_wifi()