#!/usr/bin/env python3

import minimalmodbus
import time
import serial
import pynmea2
import csv
from stats import prstats
from datetime import datetime, timezone
# from pynmea2 import nmea_utils


# get the PR up and running
print("Connecting to PR...")
while True:
    try:
        instrument = minimalmodbus.Instrument('/dev/tty-pr', 1)
        instrument.serial.baudrate = 115200
        print("...connected")
        break
    except:
        print("...retrying")
        time.sleep(1)

# start listening to the CA
print("Connecting to CA...")
while True:
    try:
        ca_serial = serial.Serial('/dev/tty-ca', 9600, timeout=0.5)
        print("...connected")
        break
    except:
        print("...retrying")
        time.sleep(1)

# start listening to the GPS
print("Connecting to GPS...")
while True:
    try:
        # TODO: GPS setup, satellite acquisition
        #gps_serial = serial.Serial('/dev/SOMETHING', baudrate=9600, timeout=0.5)
        print("...connected")
        break
    except:
        print("...retrying")
        time.sleep(1)


# The data is intended to be imported into Telemetry Overlay, here are some manual excerpts
# about how they handle generic CSV files for telemetry data:
#
# --------------------------------------------------------------------------------------------------------
# CSV files from Telemetry Extractor v2.0 and newer are also well supported. CSV files from previous
# versions of Telemetry Extractor may need manual tweaking.
#
# The first row contains the headers and requires at least utc (ms) (unix time in milliseconds)
# OR date (date-time text formatted as YYYY-MM-DDTHH:mm:ss.sssZ) OR time (ms) (video time in milliseconds)
# OR time (s) (video time in seconds) OR timecode (video time as HH:mm:ss.sss).
#
# Using the following supported units will enable unit conversion within the program
# + Speed: km/h, mph, m/s, kn, ft/min, 1000 fpm, 100 fpm, m/min, min/km, min/mi, m/h, ft/s, ft/h
# + Distance: m, km, mi, ft, NM, in, STA, yd
# + Acceleration: m/s², g, ft/s²
# + Rotation: rad/s, rpm, rpm x1000, deg/s, spm
# + Frequency: Hz, KHz, Mhz, GHz
# + Percent: %, proportion, per mille
# + Angle: deg, rad, °, :1
# + Temperature: °C, °F, K
# + Pressure: Pa, mb, hPa, psi, kPa, inHg, bar
# + Power: W, hp, mW, kW, MW
# + Time: h, min, s, ms, μs
# + Flow: LPH, GPH, lb/min
# + Volume: L, dL, cL, mL, hL, gal, cm³, cc
# + Text: text
# --------------------------------------------------------------------------------------------------------
#
# As such, you will find that I've "relabeled" several of the stats for the CA, PR, and GPS to match the
# unit formats above. Some don't exist (like (A) for Amps), but I figure it's best to at least have them
# in case they do get supported at some point

# gps headers
gps_headers = ["date", "lat (deg)", "lon (deg)", "alt (m)"]

# headers
# TODO: is RPM human pedal cadence, or wheel rpm? Probably human...
ca_headers = ["Amp Hours (ah)", "Voltage (V)", "Amps (A)", "Speed (km/h)", "Distance (km)", "Temp (°C)",
              "Cadence (rpm)", "Human Watts (W)", "Human Power (NM)", "Throttle In (V)", "Throttle Out (V)",
              "AuxA", "AuxB", "Flags (text)"]
# 13.869  83.97   0.00    0.00    33.976  22.2    0.0     0       0.0     0.84    1.15    0.00    20.0    1

# pr headers
pr_headers = [item.get('name') for item in prstats]

# one big header
headers = gps_headers + ca_headers + pr_headers

# start the log file
# TODO: when not wifi connected; need to determine filename based on something else.
#       Maybe we wait until there is a GPS lock and we can extract date/time from GPS?
log_file_name = '/app/logs/' + str(int(datetime.now().timestamp())) + '.csv'
print(f'Starting CSV log file ({log_file_name})')
csvfile = open(log_file_name, 'w', newline='')
csvwriter = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
csvwriter.writerow(headers)
csvfile.flush()

while True:

    # reset our stats holder each time
    compiled_stats = []

    # TODO: TEST Gather the GPS coordinates
    # The way GPS works is that it spits out a stream of NMEA data. Each line has a prefix and then
    # specifically formatted data for that message type. We're going to end up interested in a few
    # data types to get all the details we need; namely:
    # - GGA
    # - RMC
    # The first message contains the majority of the lat/lon/etc data we want, meanwhile
    # the RMC message critically contains the DATE object. We need this since we can't rely
    # on the rPi since it doesn't have an RTC with battery backup. Thus, when not connected
    # to your wifi (ie, out on a ride) you have no idea what the date/time is.
    #
    # With that in mind, this means we need to read multiple lines from the GPS serial connection
    # till we find at least one of each of the messages above so we can cobble together the full
    # timestamp (UTC based, ISO 8601 format)
    # ts, lat, lon, alt
    gps_data = [None, None, None, None]
    attempts = 0

    # # clear the buffer so we read the most recent data
    # gps_serial.reset_input_buffer()
    # while True:
    #     # if we've got all the data, cut out
    #     if any(x is None for x in gps_data) or attempts >= 10:
    #         break
    #     attempts += 1
    #
    #     sentence = gps_serial.readline().decode('utf-8')
    #     key = sentence[1:6]
    #     data = pynmea2.parse(sentence)
    #
    #     if hasattr(data, "datestamp") and hasattr(data, "timestamp"):
    #         # convert the funky NMEA date and time into a standard ISO variant
    #         py_date = datetime.combine(pynmea2.datestamp(data.datestamp), pynmea2.timestamp(data.timestamp))
    #         gps_data[0] = py_date.isoformat() + "Z"
    #     if hasattr(data, "latitude"):
    #         gps_data[1] = data.latitude
    #     if hasattr(data, "longitude"):
    #         gps_data[2] = data.longitude
    #     if hasattr(data, "altitude"):
    #         gps_data[3] = data.altitude

    # Fake
    gps_data = [int(datetime.now().timestamp()*1000), 1, 2, 15]
    compiled_stats += gps_data

    # Each time we loop; clear the CA buffer and fetch the next full line; this way we have the latest data.
    # To "clean up" the data, we decode it from the raw data, strip off any whitespace,
    # and then split it by the (\t) tabs
    ca_serial.reset_input_buffer()
    # throw away one line; likely incomplete
    ca_serial.readline()
    # use the next one
    ca_stats = ca_serial.readline().decode().strip().split("\t")

    if len(ca_stats) != len(ca_headers):
        # TODO: throw some kind of error?
        #       these *should* be the same length, since we don't have a way of knowing
        #       what data the CA is spitting out unless it matches out expected count
        print("ca stats wrong", len(ca_stats), len(ca_headers))
        ca_stats = [None] * len(ca_headers)

    compiled_stats += ca_stats

    # gather all the PR stats
    # note: this one doesn't need to "clear" any buffers because it's a call/response system instead
    for stat in prstats:
        val = instrument.read_register(stat.get('address'), 0, signed=stat.get('isSigned', False))
        # there are two "types" of stats: plain integer like values, some of which are "scaled" by a factor
        if stat.get('type') == "independent":
            scale = stat.get('scale', 0)
            if scale:
                val = val / scale
        # And an int which is actually a bitmap of true/false values
        # I'm not decoding these currently; since that would balloon the CSV rows quite a bit
        # and, aside from debugging purposes, I'm not convinced of their value
        else:
            val = format(val, "016b")

        # jam it all into the row data
        compiled_stats.append(val)

    # Format all the data into one cohesive format and save it
    print(compiled_stats)

    # send it out to the csvfile and flush it to disk
    csvwriter.writerow(compiled_stats)
    csvfile.flush()

    # time.sleep() is basic, could probably be a bit more advanced here (by, like, trying to hit N records, per second
    # and accounting for the sleep time calculated by how long it's been since last...but....whatever :D)
    time.sleep(0.050)
