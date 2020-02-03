
docker save hotel_splitter:v2 >hotel_splitterv2.tar

scp hotel_splitterv2.tar ccdb-dev:

# on ccdb-dev
docker load -i hotel_splitterv2.tar
