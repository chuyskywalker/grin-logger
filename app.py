#!/usr/bin/env python3
from random import randint

import minimalmodbus
import time
import serial
import pynmea2
import csv
import os
import board
import digitalio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306

from stats import prstats
from datetime import datetime, timezone

# Define the Reset Pin
oled_reset = digitalio.DigitalInOut(board.D4)

# Display Parameters
WIDTH = 128
HEIGHT = 64
BORDER = 5

# Use for I2C.
i2c = board.I2C()
oled_ready = False
while not oled_ready:
    try:
        oled = adafruit_ssd1306.SSD1306_I2C(WIDTH, HEIGHT, i2c, addr=0x3C, reset=oled_reset)
        oled_ready = True
    except:
        print("Awaiting OLED ready...")
        time.sleep(1)

# Create blank image for drawing.
# Make sure to create image with mode '1' for 1-bit color.
image = Image.new("1", (oled.width, oled.height))

# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)
font = ImageFont.truetype('PixelOperator.ttf', 16)





pr_serial = serial.Serial(None, baudrate=115200, timeout=0.5)
ca_serial = serial.Serial(None, baudrate=9600, timeout=0.5)
gps_serial = serial.Serial(None, baudrate=9600, timeout=0.5)

pr_serial.port = os.getenv('pr_serial', '/dev/serial/by-id/find-pr-value-and-set-in-env')
ca_serial.port = os.getenv('ca_serial', '/dev/serial/by-id/find-ca-value-and-set-in-env')
gps_serial.port = os.getenv('gps_serial', '/dev/ttyACM0')
speed_units = os.getenv('speed_units', 'km/h')

use_oled = os.getenv('oled', '0')

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

script_start = datetime.now()
sat_count = lat = lon = "???"
gps_state = pr_state = ca_state = 'N'
record_count = 0

while True:

    if use_oled == '1':
        try:
            duration = datetime.now() - script_start
            seconds_passed = duration.total_seconds()
            (minutes, seconds) = divmod(seconds_passed, 60)

            draw.rectangle((0, 0, oled.width, oled.height), outline=0, fill=0)
            draw.text((0, 0), 'DUR: {:02}:{:02}'.format(int(minutes), int(seconds)), font=font, fill=255)
            draw.text((0, 16), f'SAT: {sat_count}  LN: {record_count:,}', font=font, fill=255)
            draw.text((0, 32), f'GPS: {gps_state}  PR: {pr_state}  CA: {ca_state}', font=font, fill=255)
            draw.text((0, 48), f'{lat}, {lon}', font=font, fill=255)

            oled.image(image)
            oled.show()

        except Exception as e:
            print('could not update screen: ', e)

    try:
        # The way GPS works is that it spits out a stream of NMEA messages. Each line has a prefix and then
        # specifically formatted data for that message type. We're interested in a few data types to get all
        # the details we need; namely:
        # - GGA
        # - RMC
        # The first message contains the majority of the lat/lon/etc data we want, meanwhile
        # the RMC message critically contains the DATE and TIME info. We need this since we can't rely
        # on the rPi since it doesn't have an RTC with battery backup. Thus, when not connected
        # to your wifi (ie, out on a ride) you have no idea what the date/time is.
        #
        # With that in mind, this means we need to read multiple lines from the GPS serial connection
        # till we find at least one of each of the messages above so we can cobble together the full
        # timestamp (UTC based, ISO 8601 format)
        #
        # Every time we need the GGA, but we only need a valid RMC once to get & set the time.

        # pre-populate an empty set of stats
        gps_stats = [None] * len(gps_headers)

        # track gga_read so that if we see that message, we can exit the loop
        gga_read = False

        # only try SO many times
        attempts = 0

        # open the serial port if it's been lost/failed
        if not gps_serial.is_open:
            gps_serial.open()

        # clear the buffer so we read the most recent data
        gps_serial.reset_input_buffer()

        # loop read messages till we've fetched all our data
        while True:

            # if we have the GGA and the time is already set, we're done
            if gga_read and time_set:
                break

            # also bust out if we've tried too many times
            if attempts >= 25:
                print("gps fail, too many message")
                break

            # increment the attempt counter
            attempts += 1

            # get some DATA
            line = gps_serial.readline().decode('utf-8')

            # skip empty lines; usually happens after reset
            if line == '':
                continue

            # parse the line
            try:
                msg = pynmea2.parse(line)
            except Exception as e:
                print('failed to understand message, skipping it: ', e)
                continue

            # print(repr(msg))

            # We only need the RMC message once to set the date/time
            if type(msg) is pynmea2.RMC and not time_set:
                if (hasattr(msg, "datestamp") and hasattr(msg, "timestamp")
                        and msg.datestamp not in [None, '', 0]
                        and msg.timestamp not in [None, '', 0]):
                    py_date = datetime.combine(msg.datestamp, msg.timestamp)
                    ts = py_date.isoformat().replace('+00:00', 'Z')

                    # update system time and reset timer
                    print(f'Got time from GPS, setting to: {ts}')
                    os.system(f'date -u -s"{ts}"')
                    time_set = True
                    script_start = datetime.now()

            # otherwise the message we really need is GGA for lat/lon/sats/etc
            elif type(msg) is pynmea2.GGA:
                gga_read = True
                if hasattr(msg, "latitude") and msg.latitude not in [None, '', 0]:
                    gps_stats[0] = round(msg.latitude, 6)
                    lat = round(msg.latitude, 4)
                if hasattr(msg, "longitude") and msg.longitude not in [None, '', 0]:
                    gps_stats[1] = round(msg.longitude, 6)
                    lon = round(msg.longitude, 4)
                if hasattr(msg, "altitude") and msg.altitude not in [None, '', 0]:
                    gps_stats[2] = round(float(msg.altitude), 2)
                if hasattr(msg, "num_sats") and msg.num_sats not in [None, '', 0]:
                    gps_stats[3] = sat_count = int(msg.num_sats)
                if hasattr(msg, "horizontal_dil") and msg.horizontal_dil not in [None, '', 0]:
                    gps_stats[4] = round(float(msg.horizontal_dil), 3)
                if hasattr(msg, "gps_qual") and msg.gps_qual not in [None, '', 0]:
                    gps_stats[5] = msg.gps_qual

            # every other message is just noise to us
            else:
                # print("skipped message (" + msg.__class__.__name__ + ") we don't need")
                continue

    except Exception as e:
        print('gps data failed: ', e)
        gps_stats = [None] * len(gps_headers)
        gps_serial.close()
        time.sleep(0.1)
        gps_state = 'N'

    # once out of the loop; maybe we read a GGA message, but it was bunk
    # or something else has gone wrong to miss some data. Instead of logging halfway, just dump this one

    if any(x is None for x in gps_stats):
        print('GPS data incomplete; invalidating', gps_stats)
        gps_stats = [None] * len(gps_headers)
        gps_state = 'N'
    else:
        gps_state = 'Y'

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
        ca_stats_raw = ca_serial.readline().decode().strip().split("\t")
        ca_state = 'Y'

        # translate the raw stats into better types
        ca_stats = [
            round(float(ca_stats_raw[0]), 2),   # "Amp Hours (ah)",           '30.15',
            round(float(ca_stats_raw[1]), 2),   # "Voltage (V)",              '77.59',
            round(float(ca_stats_raw[2]), 2),   # "Amps (A)",                 '0.10',
            round(float(ca_stats_raw[3]), 2),   # f'Speed ({speed_units})',   '0.00',
            # ## skip distance; gps will have it via track points and it's another unknown value
            # #round(float(ca_stats_raw[4]), 2),  # "Distance (km)",            '23.1',
            round(float(ca_stats_raw[5]), 2),   # "Temp (°C)",                '20.5',
            int(float(ca_stats_raw[6])),   # "Cadence (rpm)",            '0.0',
            int(float(ca_stats_raw[7])),   # "Human Watts (W)",          '0',
            round(float(ca_stats_raw[8]), 2),   # "Human Power (NM)",         '0.0',
            round(float(ca_stats_raw[9]), 2),   # "Throttle In (V)",          '0.83',
            round(float(ca_stats_raw[10]), 2),  # "Throttle Out (V)",         '1.15',
            round(float(ca_stats_raw[11]), 2),  # "AuxA",                     '54.2',
            round(float(ca_stats_raw[12]), 2),  # "AuxB",                     '20.0',
            ca_stats_raw[13],                   # "Flags",                    '1w',
        ]

        if len(ca_stats) != len(ca_headers):
            raise Exception(f"ca stat lengths don't match headers {len(ca_stats)} != {len(ca_headers)}")

    except Exception as e:
        print('ca stats failed: ', e)
        ca_stats = [None] * len(ca_headers)
        ca_serial.close()
        time.sleep(0.1)
        ca_state = 'N'

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

            pr_state = 'Y'
    except Exception as e:
        print("pr stats failed: ", e)
        pr_stats = [None] * len(pr_headers)
        pr_state = 'N'
        if instrument is not None:
            instrument.serial.close()
            time.sleep(0.1)

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
    record_count += 1

    # time.sleep() is basic, could probably be a bit more advanced here (by, like, trying to hit N records, per second
    # and accounting for the sleep time calculated by how long it's been since last...but....whatever :D)
    time.sleep(0.1)
