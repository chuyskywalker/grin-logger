# Grin Logger

A python container designed to log data from a Grin Phaserunner (PR), Cycle Analyst (CA), and a GPS unit.

## What It Does

Based on a RaspberryPi, some TTL/USB cables and a GPS antenna, this will log data from the PR, CA, and GPS as one whole CSV formatted file. This file can be imported and manipulated however you want, but it is intended as a direct input to Telemetry Overlay software. As currently built, it tracks these fields:

```
date,lat (deg),lon (deg),alt (m),
Amp Hours (ah),Voltage (V),Amps (A),Speed (km/h),Distance (km),Temp (°C),Cadence (rpm),Human Watts (W),Human Power (NM),Throttle In (V),Throttle Out (V),AuxA,AuxB,Flags (text),
Faults (text),Controller Temperature (°C),Vehicle Speed (km/h),Motor Temperature (°C),Motor Current (A),Motor RPM (RPM),Motor Speed (%),Battery Voltage (V),Battery Current (A),Battery State of Charge (%),Battery Power (W),Last Fault (text),Throttle Voltage (V),Brake 1 Voltage (V),Brake 2 Voltage (V),Phase A Current (A),Phase B Current (A),Phase C Current (A),Phase A Voltage (V),Phase B Voltage (V),Phase C Voltage (V),Wheel Speed Sensor Based (RPM),Wheel Speed Motor Based (RPM),Measured Wheel Speed (RPM)
```

The first four are GPS, the next 14 are from the CA, and the remainder are from the PR.

## Setup

I am running a RaspberryPi 4 Model B; useful as it has 4 fullsized USB ports. I have the two TTL-to-USB cords from Grin -- one to the PR the other to the CA. The GPS and a wifi take up the other two USB ports.

The install on the rPi is a standard Raspian install. After that, I also installed Docker in order to keep the python app contained.

The app relies on a few synmlinked TTY `/dev/` ports. Plug in the PR, look under `/dev/serial/by-id/` for the new entry and add a symlink for it such as:

```bash
ln -s /dev/serial/by-id/usb-FTDI_FT230X_Basic_UART_DO01KYGI-if00-port0 /dev/tty-pr
```

Then plug in the CA and do the same, but for `/dev/tty-ca`.

_(todo: instructions for GPS)_

To run the app interactively:

```bash
# the build command need only be run once...
docker build -t bikelogger .
docker run -ti --rm --privileged \
  -v /dev:/dev \
  -v /share/app:/app \
  -w /app bikelogger bash
```

You likely need to change `/share/app` to where you've placed these application files on the host. You should also create a `logs` directory in the same location.

> **WARNING** This runs in privledged mode to skirt around USB mounting/unmounting issues and maps the entire `/dev` into the container. Since this is really the only thing designed to run on the machine, though, hassling with the other work arounds wasn't worth the head ache.

One running, you should see a log file generated under `logs` -- you can tail this or do a fancy watch command like this:

```bash
watch -n1 -x bash -c "paste <(head -n 1 1728684428.csv | tr ',' '\n' | tr -d '\r') <(tail -n 1 1728684428.csv  | tr ',' '\n' | tr -d '\r') | column -s $'\t' -t"
```

Which formats it into a display like output.