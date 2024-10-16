# Grin Logger

A python container designed to log data from a Grin Phaserunner (PR), Cycle Analyst (CA), and a GPS unit.

## What It Does

Based on a [RaspberryPi][pi][^1], some [TTL/USB cables][ttlusb] and [a GPS antenna][gps], this will log data from the PR, CA, and GPS as one whole CSV formatted file. This file can be imported and manipulated however you want, but it is intended as a direct input to Telemetry Overlay software.

## Setup

I am running a RaspberryPi 4 Model B; useful as it has 4 fullsized USB ports. I have the two TTL-to-USB cords from Grin -- one to the PR the other to the CA. The GPS takes up a third port and I'm using onboard wifi to connect to my local network when in range.

The OS on the rPi is a standard Raspian install. After that, I also installed Docker in order to keep the python app contained.

I do recommend removing `timesyncd` so the script can use the GPS date to set the clock on the machine after boot.

```bash
apt-get remove systemd-timesyncd
```

> _Note: GPS date sync in this naive sense (without PPS) is a bit inaccurate, but we're talking ms (milliseconds)! For the purposes of data logging a bike ride, it's WELL within acceptable drift)_

To run the app interactively:

```bash
# the build command need only be run once...
docker build -t bikelogger .
docker run -ti --rm --privileged \
  -v /dev:/dev \
  -v /share/app:/app \
  -w /app bikelogger bash
```

Change `/share/app` to where you've placed these application files on the host. You should also create a `logs` directory in the same location.

> **WARNING** This runs in privileged mode to skirt around USB mounting/unmounting issues and maps the entire `/dev` into the container. Since this is really the only thing designed to run on the machine, though, hassling with the other workarounds wasn't worth the headache.

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

### ENV Params

There are several things that will be different from install-to-install. At the least, your device address/locations will be different and you may or may not have wired up a small SSD1306 OLED screen for live stats.

Here are the ENV properties you can set:

| ENV           | Example                 |
|---------------|-------------------------|
| `pr_serial`   | /dev/serial/by-id/yours |
| `ca_serial`   | /dev/serial/by-id/yours |
| `gps_serial`  | /dev/tty-yours          |
| `speed_units` | `mp/h` or `kp/h`        |
| `oled`        | 0 or 1                  |

The serial ports are pretty straight forward; set those to match how the plugs show up on your system. 

The `speed_units` is there because we record speed from the CA, but the CA reports speed in whatever unit you have the unit configured for, thus to log it in the correct units, you need to supply this.

Finally, if you have wired in a 128x64 OLED mini screen, the script can output some basic stats to the screen to let you know the state of the recording.

You can add these to the docker run commands like so:
```bash
docker run ... \
  -e 'pr_serial=/dev/tty/...' \
  -e 'ca_serial=/dev/tty/...' \
  -e 'gps_serial=/dev/tty/...' \
  -e 'speed_units=mp/h' \
  -e 'oled=1' \
  ...
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