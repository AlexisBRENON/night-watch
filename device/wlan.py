import asyncio
from config import Configuration

import network


async def wlan():
    config = Configuration.load()

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    access_point_ssids = {str(ap[0]) for ap in wlan.scan()}
    for net in config.networks:
        if net.ssid in access_point_ssids:
            print(f"Connecting to known network {net.ssid}...")
            wlan.connect(net.ssid, net.key)
            while wlan.isconnected() == False:
                await asyncio.sleep(1)
            break

    if not wlan.isconnected():
        wlan.active(False)
        del wlan
        print("Setting up access point...")
        wlan = network.WLAN(network.AP_IF)
        wlan.active(True)
        wlan.config(essid="NightWatch", password="123456789")

        print("Waiting access point active state...")
        while not wlan.active():
            await asyncio.sleep(1)

    print(f"Status: {wlan.status()}")
    print(wlan.ifconfig())
    return wlan
