

# easier to run in priv mode than to start up and fail because devices aren't yet ready
docker run -ti --rm --privileged \
  -v /share/app:/app -v /dev:/dev \
  -e 'pr_serial=/dev/serial/by-id/usb-FTDI_FT230X_Basic_UART_DO01LIUZ-if00-port0' \
  -e 'ca_serial=/dev/serial/by-id/usb-FTDI_FT230X_Basic_UART_DO01KYGI-if00-port0' \
  -e 'gps_serial=/dev/ttyACM0' \
  -e 'speed_units=mp/h' \
  -e 'oled=1' \
  -w /app \
  bikelogger bash


# reformat the contents so it's the head of the CSV with table contents of the last line
# watch -n1 -x bash -c "paste <(head -n 1 1728684428.csv | tr ',' '\n' | tr -d '\r') <(tail -n 1 1728684428.csv  | tr ',' '\n' | tr -d '\r') | column -s $'\t' -t"

#docker run --restart=always --detach --privileged --name bikelogger \
#  -v /share/app:/app -v /dev:/dev -w /app \
#  -e 'pr_serial=/dev/serial/by-id/usb-FTDI_FT230X_Basic_UART_DO01LIUZ-if00-port0' \
#  -e 'ca_serial=/dev/serial/by-id/usb-FTDI_FT230X_Basic_UART_DO01KYGI-if00-port0' \
#  -e 'gps_serial=/dev/ttyACM0' \
#  -e 'speed_units=mp/h' \
#  -e 'oled=1' \
#  bikelogger \
#  python -u app.py