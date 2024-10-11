
# easier to run in priv mode than to start up and fail because devices aren't yet ready
docker run -ti --rm -v /share/app:/app --privileged -v /dev:/dev -w /app bikelogger bash


# reformat the contents so it's the head of the CSV with table contents of the last line
# watch -n1 -x bash -c "paste <(head -n 1 1728684428.csv | tr ',' '\n' | tr -d '\r') <(tail -n 1 1728684428.csv  | tr ',' '\n' | tr -d '\r') | column -s $'\t' -t"