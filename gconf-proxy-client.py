#!/usr/bin/env python

import dbus

gconf_key = "/org/gnome/GConf/apps/maemo-mapper/route_dl_url"

bus = dbus.SessionBus()

try:
    gconf_key_object = bus.get_object("/org/gnome/GConf", "org.gnome.GConf")
    iface = dbus.Interface(gconf_key_object, 'org.gnome.GConf')
except dbus.DBusException:
    print_exc()

#value = iface.getString(gconf_key)

#print ("Value of GConf key %s is %s" % (gconf_key, value))
