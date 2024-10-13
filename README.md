# Grin Logger

A python container designed to log data from a Grin Phaserunner (PR), Cycle Analyst (CA), and a GPS unit.

## What It Does

Based on a [RaspberryPi][pi][^1], some [TTL/USB cables][ttlusb] and [a GPS antenna][gps], this will log data from the PR, CA, and GPS as one whole CSV formatted file. This file can be imported and manipulated however you want, but it is intended as a direct input to Telemetry Overlay software. As currently built, it tracks these fields:

```
date,lat (deg),lon (deg),alt (m),satellites,gps dop,gps fix,
Amp Hours (ah),Voltage (V),Amps (A),Speed (km/h),Distance (km),Temp (°C),Cadence (rpm),Human Watts (W),Human Power (NM),Throttle In (V),Throttle Out (V),AuxA,AuxB,Flags (text),
Faults (text),Controller Temperature (°C),Vehicle Speed (km/h),Motor Temperature (°C),Motor Current (A),Motor RPM (RPM),Motor Speed (%),Battery Voltage (V),Battery Current (A),Battery State of Charge (%),Battery Power (W),Last Fault (text),Throttle Voltage (V),Brake 1 Voltage (V),Brake 2 Voltage (V),Phase A Current (A),Phase B Current (A),Phase C Current (A),Phase A Voltage (V),Phase B Voltage (V),Phase C Voltage (V),Wheel Speed Sensor Based (RPM),Wheel Speed Motor Based (RPM),Measured Wheel Speed (RPM)
```

That's GPS, followed by CA, and the remainder are from the PR.

## Setup

I am running a RaspberryPi 4 Model B; useful as it has 4 fullsized USB ports. I have the two TTL-to-USB cords from Grin -- one to the PR the other to the CA. The GPS takes up a third port and I'm using onboard wifi to connect to my local network when in range.

The OS on the rPi is a standard Raspian install. After that, I also installed Docker in order to keep the python app contained.

When you grab the code you will need to edit the locations for the PR and CA ttl cables. I've found they are uniquely labeled and easy to reference from the `/dev/serial/by-id/` entries. Plug them in one-at-a-time and it's easy to grab their ID's. (Apparently, you could auto-map these to something nicer like `/dev/tty-pc` if you took the time to figure out udev or something. I haven't bothered.) At some point, I'll probably allow for the values to be passed into the container as ENV properties, but for now they are just hardcoded.

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

> **WARNING** This runs in privledged mode to skirt around USB mounting/unmounting issues and maps the entire `/dev` into the container. Since this is really the only thing designed to run on the machine, though, hassling with the other workarounds wasn't worth the headache.

One running, you should see a log file generated under `logs` -- you can tail this or do a fancy watch command like this:

```bash
watch -n1 -x bash -c "paste <(head -n 1 1728684428.csv | tr ',' '\n' | tr -d '\r') <(tail -n 1 1728684428.csv  | tr ',' '\n' | tr -d '\r') | column -s $'\t' -t"
```

Which formats it into a display like output.

To make a version that runs as soon as the computer boots up and just starts logging, then you run this:

```bash
docker run --restart=always --detach --privileged --name bikelogger \
  -v /share/app:/app -v /dev:/dev -w /app \
  bikelogger \
  python -u app.py
```

You can watch logs from the process like this:

```bash
docker logs -f bikelogger
```

----

This was [stream-of-post developed over at the EndlessSphere forums](https://endless-sphere.com/sphere/threads/trip-data-logging-phaserunner-ca-gps.125645/).

[^1]: Note: If you use the Raspberry Pi 4, there is a "bug" in so much that if the USB ports have any back-fed power, the pi will not boot. Since the PR backfeeds on the TRRS cable a 5v intended to power a down stream device, this can potentially stop your pi logger from starting up and recording. As such, you will need to purchase a ["power stopper"](https://www.amazon.com/dp/B094G4P3P4) to disconnect the 5v coming from the PR. 

[pi]: https://www.amazon.com/dp/B07TC2BK1X
[gps]: https://www.amazon.com/dp/B01EROIUEW
[ttlusb]: https://ebikes.ca/ttl-usb-cable.html