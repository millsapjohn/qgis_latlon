from .latlon import LatLonPlugin

def classFactory(iface):
    return LatLonPlugin(iface)
