-- support
- Arch Linux
- CentOS 6.x, 7.x, 8.x, 9.x
- Debian 8.x, 9.x, 10.x, 11.x, 12.x
- Rocky Linux 8.x, 9.x
- Ubuntu 16.x, 18.x, 20.x, 22.x



-- download
wget "http://199.115.230.237:12345/lnxmon/lnxmonsrv"
wget "http://199.115.230.237:12345/lnxmon/lnxmoncli"

chmod +x lnxmonsrv
chmod +x lnxmoncli



-- server
./lnxmonsrv

./lnxmonsrv --help
./lnxmonsrv --host="127.0.0.1"
./lnxmonsrv --host="0.0.0.0"
./lnxmonsrv --port=1234
./lnxmonsrv --gzip=true
./lnxmonsrv --gzip=false



-- client
./lnxmoncli

./lnxmoncli --help
./lnxmoncli --host="127.0.0.1"
./lnxmoncli --port=1234
./lnxmoncli --project="TEST"
./lnxmoncli --debug=true



-- access
http://127.0.0.1:1234/
http://127.0.0.1:1234/?id=1&mode=0
http://127.0.0.1:1234/?id=1&mode=1
http://127.0.0.1:1234/?id=1&offset=240
http://127.0.0.1:1234/?id=1&offset=240&limit=10
http://127.0.0.1:1234/?id=1&offset=240&limit=-1
http://127.0.0.1:1234/?project=default

http://127.0.0.1:1234/api/get_projects
http://127.0.0.1:1234/api/get_hosts
http://127.0.0.1:1234/api/get_hosts?project=default
http://127.0.0.1:1234/api/get_host?id=1
http://127.0.0.1:1234/api/get_host_metric?id=1
http://127.0.0.1:1234/api/get_host_metric?id=1&offset=240
http://127.0.0.1:1234/api/get_host_metric?id=1&offset=240&limit=10
http://127.0.0.1:1234/api/get_host_metric?id=1&offset=240&limit=-1
