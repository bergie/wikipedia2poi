#!/usr/bin/python2.5
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

__author__    = "Henri Bergius <henri.bergius@iki.fi>"
__version__   = "0.0.1"
__date__      = "2007-03-06"
__copyright__ = "Copyright (c) 2007 %s. All rights reserved." % __author__
__licence__   = "LGPL"

import sqlite3
import dbus
import httplib
import os
from xml.dom.minidom import parseString

# Start with getting position from GeoClue
bus = dbus.SessionBus()
# TODO: Get the GeoClue interface to use from /schemas/apps/geoclue/position/defaultpath 
# and /schemas/apps/geoclue/position/defaultserviceGConf keys
proxy_obj = bus.get_object('org.foinse_project.geoclue.position.hostip', '/org/foinse_project/geoclue/position/hostip')
geoclue_iface = dbus.Interface(proxy_obj, 'org.foinse_project.geoclue.position')

# Get the coordinates from the service
coordinates = geoclue_iface.current_position()
# We can also use hardcoded
coordinates[0] = 60.158806494564
coordinates[1] = 24.9426341056824

print "According to GeoClue you are in %s %s." % (coordinates[0], coordinates[1])

# Make the HTTP request to the Geonames service
print "Pulling local Wikipedia pages from Geonames"
http_connection = httplib.HTTPConnection("ws.geonames.org")
http_connection.request("GET", "/findNearbyWikipedia?lat=%s" % coordinates[0] + "&lng=%s" % coordinates[1] + "&maxRows=100")
http_response = http_connection.getresponse()
# TODO: Error handling
xml = http_response.read()

def parse_entries(xml):
    dom = parseString(xml)
    entries = dom.getElementsByTagName('entry')
    results = []
    for entry in entries:
        entry_dictionary = {}
        entry_dictionary['title'] = entry.getElementsByTagName('title')[0].firstChild.data
        entry_dictionary['summary'] = entry.getElementsByTagName('summary')[0].firstChild.data + " (source: Wikipedia)"
        
        if (entry.getElementsByTagName('feature')[0].firstChild):
            entry_dictionary['feature'] = entry.getElementsByTagName('feature')[0].firstChild.data
            
        entry_dictionary['lat'] = float(entry.getElementsByTagName('lat')[0].firstChild.data)
        entry_dictionary['lon'] = float(entry.getElementsByTagName('lng')[0].firstChild.data)
        results.append(entry_dictionary)
    return results

entries = parse_entries(xml)

# Open SQLite connection
#sqlite_connection = sqlite3.connect(os.path.expanduser("~/MyDocs/.documents/poi.db"))
sqlite_connection = sqlite3.connect(os.path.expanduser("/home/user/MyDocs/.documents/poi.db"))
sqlite_cursor = sqlite_connection.cursor()
for entry in entries:
    # Check if the entry is already in database
    sql_variables = (entry["title"],)
    sqlite_cursor.execute('select poi_id from poi where label=?', sql_variables)
    existing_entry_id = sqlite_cursor.fetchall()
    if (existing_entry_id):
        print "%s is already in database, skipping" % entry["title"]
        # TODO: Update
    else:
        print "Inserting %s (%s, %s) into POI database" % (entry["title"], entry["lat"], entry["lon"])
        # TODO: Be smarter about POI categories
        sql_variables = (entry["lat"], entry["lon"], entry["title"], entry["summary"], 10)
        sqlite_cursor.execute("insert into poi (lat, lon, label, desc, cat_id) values (?, ?, ?, ?, ?)", sql_variables)

# Do our evil little easter egg
import random
sql_variables = ("Earth",)
sqlite_cursor.execute('select poi_id from poi where label=?', sql_variables)
existing_entry_id = sqlite_cursor.fetchall()
random_lat = random.uniform(-90, 90)
random_lon = random.uniform(-180, 180)
sql_variables = (random_lat, random_lon, "Earth", "Mostly Harmless", 10)
if (existing_entry_id):
    sql_variables = (random_lat, random_lon)
    sqlite_cursor.execute("update poi set lat=?,lon=? where label=\"Earth\"", sql_variables)
else:
    sqlite_cursor.execute("insert into poi (lat, lon, label, desc, cat_id) values (?, ?, ?, ?, ?)", sql_variables)

# Finally commit the database
sqlite_connection.commit()
sqlite_cursor.close()
sqlite_connection.close()