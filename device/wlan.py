import asyncio
from config import Configuration

import network


_WLAN_IS_CONNECTED = asyncio.Event()
_WLAN = None


async def get_instance():
    global _WLAN
    if _WLAN is None:
        config = Configuration.load()

        _WLAN = network.WLAN(network.STA_IF)
        _WLAN.active(True)
        access_point_ssids = {str(ap[0]) for ap in _WLAN.scan()}
        for net in config.networks:
            if net.ssid in access_point_ssids:
                print(f"Connecting to known network {net.ssid}...")
                _WLAN.connect(net.ssid, net.key)
                while not _WLAN.isconnected():
                    await asyncio.sleep(1)
                break

        if not _WLAN.isconnected():
            _WLAN.active(False)
            del _WLAN
            print("Setting up access point...")
            _WLAN = network.WLAN(network.AP_IF)
            _WLAN.active(True)
            _WLAN.config(essid="NightWatch", password="123456789")

            print("Waiting access point active state...")
            while not _WLAN.active():
                await asyncio.sleep(1)

        print(f"Status: {_WLAN.status()}")
        print(_WLAN.ifconfig())
        _WLAN_IS_CONNECTED.set()
    return _WLAN


async def wait_for_connection():
    await _WLAN_IS_CONNECTED.wait()
