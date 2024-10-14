#!/usr/bin/env python3

import minimalmodbus
import time
import serial
import pynmea2
import csv
import os

from stats import prstats
from datetime import datetime, timezone


pr_serial = serial.Serial(None, baudrate=115200, timeout=0.5)
ca_serial = serial.Serial(None, baudrate=9600, timeout=0.5)
gps_serial = serial.Serial(None, baudrate=9600, timeout=0.5)

pr_serial.port = os.getenv('pr_serial', '/dev/serial/by-id/usb-FTDI_FT230X_Basic_UART_DO01LIUZ-if00-port0')
ca_serial.port = os.getenv('ca_serial', '/dev/serial/by-id/usb-FTDI_FT230X_Basic_UART_DO01KYGI-if00-port0')
gps_serial.port = os.getenv('gps_serial', '/dev/ttyACM0')
speed_units = os.getenv('speed_units', 'km/h')

# the minimalmodbus will not start with a closed serial, so we leave it as none for now
instrument = None
csvwriter = None


# The data is intended to be imported into Telemetry Overlay, here are some manual excerpts
# about how they handle generic CSV files for telemetry data:
#
# --------------------------------------------------------------------------------------------------------
# https://goprotelemetryextractor.com/docs/telemetry-overlay-manual.pdf
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
#
# Some GPS quality columns are also supported for dynamically filtering out bad GPS data:
# "satellites" (nubmer of gps satellites),
# "gps dop" (dillution of precision),
# "gps fix" (type of GPS fix: a number from 0 to 3)
# --------------------------------------------------------------------------------------------------------
#
# As such, you will find that I've "relabeled" several of the stats for the CA, PR, and GPS to match the
# unit formats above. Some don't exist (like (A) for Amps), but I figure it's best to at least have them
# in case they do get supported at some point

# gps headers
gps_headers = ["lat (deg)", "lon (deg)", "alt (m)", "satellites", "gps dop", "gps fix"]

# CA headers
ca_headers = ["Amp Hours (ah)",
              "Voltage (V)",
              "Amps (A)",
              f'Speed ({speed_units})',
              # "Distance (km)", ## skip!
              "Temp (°C)",
              "Cadence (rpm)",
              "Human Watts (W)",
              "Human Power (NM)",
              "Throttle In (V)",
              "Throttle Out (V)",
              "AuxA",
              "AuxB",
              "Flags (text)"
              ]
# 13.869  83.97   0.00    0.00    33.976  22.2    0.0     0       0.0     0.84    1.15    0.00    20.0    1

# pr headers
pr_headers = [item.get('name') for item in prstats]

# one big header
headers = ["date"] + gps_headers + ca_headers + pr_headers

# time set
time_set = False

while True:

    try:
        # The way GPS works is that it spits out a stream of NMEA messages. Each line has a prefix and then
        # specifically formatted data for that message type. We're interested in a few data types to get all
        # the details we need; namely:
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

        # preset the stats as nones so we can test "if all are no long None, we're good!"
        # also setup attempts so we don't spin our wheels here forever if the message queue gets wonky
        gps_stats = [None] * len(gps_headers)
        attempts = 0

        # open the serial port if it's been lost/failed
        if not gps_serial.is_open:
            gps_serial.open()

        # clear the buffer so we read the most recent data
        gps_serial.reset_input_buffer()

        # loop read messages till we've fetched all our data
        while True:
            # if we've got all the data, break the line reading loop
            if not any(x is None for x in gps_stats):
                break

            # also bust out if we've tried too many times, emptying the collected data
            if attempts >= 10:
                gps_stats = [None] * len(gps_headers)
                break

            # increment the attempt counter
            attempts += 1

            # get some DATA
            line = gps_serial.readline().decode('utf-8')

            # skip empty lines; usually happens after reset
            if line == '':
                continue

            # parse the line
            msg = pynmea2.parse(line)

            # skip any message which is not a GGA/RMC since we only need those two types
            if type(msg) not in [pynmea2.GGA, pynmea2.RMC]:
                # print("skipped message (" + msg.__class__.__name__ + ") we don't need")
                continue

            # print(repr(msg))

            # collect whatever data we can from the messages
            # yes, RMC and GGA both have lat/long; we can take the values from either, they'll be the same
            # it's just different message types from years of caked on different vendor requirements
            # each message type has a bit of the data we need, so we seek both.
            # todo: the indexing by int here is...a brittle solution

            # if we have the date/time, use that to sync the system to current
            if hasattr(msg, "datestamp") and hasattr(msg, "timestamp"):
                py_date = datetime.combine(msg.datestamp, msg.timestamp)
                ts = py_date.isoformat().replace('+00:00', 'Z')

                if not time_set:
                    os.system(f'date -u -s"{ts}"')
                    time_set = True

            if hasattr(msg, "latitude"):
                gps_stats[0] = round(msg.latitude, 6)
            if hasattr(msg, "longitude"):
                gps_stats[1] = round(msg.longitude, 6)
            if hasattr(msg, "altitude"):
                gps_stats[2] = msg.altitude
            if hasattr(msg, "num_sats"):
                gps_stats[3] = msg.num_sats
            if hasattr(msg, "horizontal_dil"):
                gps_stats[4] = msg.horizontal_dil
            if hasattr(msg, "gps_qual"):
                gps_stats[5] = msg.gps_qual

    except Exception as e:
        print('gps data failed: ', e)
        gps_stats = [None] * len(gps_headers)
        gps_serial.close()

    try:
        # open the serial port if it's been lost/failed
        if not ca_serial.is_open:
            ca_serial.open()
        # Each time we loop; clear the CA buffer and fetch the next full line; this way we have the latest data.
        ca_serial.reset_input_buffer()
        # throw away one line; likely incomplete, read a line and toss it using the next one
        ca_serial.readline()
        # To "clean up" the data, we decode it from the raw data, strip off any whitespace,
        # and then split it by the (\t) tabs
        ca_stats = ca_serial.readline().decode().strip().split("\t")
        ## remove list item 5th item (index 4), "distance traveled"
        ca_stats.pop(4)

        if len(ca_stats) != len(ca_headers):
            raise Exception(f"ca stat lengths don't match headers {len(ca_stats)} != {len(ca_headers)}")

    except Exception as e:
        print('ca stats failed: ', e)
        ca_stats = [None] * len(ca_headers)
        ca_serial.close()

    try:
        # set up the instrument
        if instrument is None:
            pr_serial.open()
            instrument = minimalmodbus.Instrument(pr_serial, 1)

        # open the serial port if it's been lost/failed
        if not instrument.serial.is_open:
            instrument.serial.open()

        # gather all the PR stats
        # note: this one doesn't need to "clear" any buffers because it's a call/response system instead
        pr_stats = []
        for stat in prstats:
            val = instrument.read_register(stat.get('address'), 0, signed=stat.get('isSigned', False))
            # there are two "types" of stats: plain integer like values, some of which are "scaled" by a factor
            if stat.get('type') == "independent":
                scale = stat.get('scale', 0)
                if scale:
                    val = val / scale
                if stat.get('round', None) is not None:  # could use ('round', False) for a small if, but then round:0 would fail
                    val = round(val, stat.get('round'))
            # And an int which is actually a bitmap of true/false values
            # I'm not decoding these currently; since that would balloon the CSV rows quite a bit
            # and, aside from debugging purposes, I'm not convinced of their value
            else:
                val = format(val, "016b")

            # jam it all into the row data
            pr_stats.append(val)
    except Exception as e:
        print("pr stats failed: ", e)
        pr_stats = [None] * len(pr_headers)
        if instrument is not None:
            instrument.serial.close()

    # start the csvwriter if we have a date to use
    current_date = datetime.now(timezone.utc)

    if csvwriter is None:
        if not time_set:
            print("No date yet, can't start log file")
            continue

        filename_id = current_date.strftime("%Y_%m_%d_%H_%M_%S")
        log_file_name = f'/app/logs/{filename_id}.csv'

        print(f'Starting CSV log file ({log_file_name})')
        csvfile = open(log_file_name, 'w', newline='')
        csvwriter = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        csvwriter.writerow(headers)

    compiled_stats = [current_date.isoformat().replace('+00:00', 'Z')] + gps_stats + ca_stats + pr_stats
    print(compiled_stats)

    # send it out to the csvfile and flush it to disk
    csvwriter.writerow(compiled_stats)
    csvfile.flush()

    # time.sleep() is basic, could probably be a bit more advanced here (by, like, trying to hit N records, per second
    # and accounting for the sleep time calculated by how long it's been since last...but....whatever :D)
    time.sleep(0.001)
