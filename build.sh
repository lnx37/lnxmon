#!/bin/bash

set -e
set -o pipefail
set -u
set -x

cd "$(dirname "$0")"

date

printf "\n-- $(date) -- starting --\n"

[ -d build ] && rm -rf build
mkdir -p build/lib

go run build.go
tar xzf lib/go-sqlite3-*.tar.gz -C build/lib
mv build/lib/go-sqlite3-1.14.16 build/lib/go-sqlite3

printf "\n-- $(date) -- building --\n"

# apt-get install gcc glibc-static
# yum install gcc glibc-static
# yum install binutils-devel
GO111MODULE=off go build -ldflags="-s -w -linkmode=external -extldflags=-static" -o build/lnxmonsrv build/lnxmonsrv.go
GO111MODULE=off go build -ldflags="-s -w -linkmode=external -extldflags=-static" -o build/lnxmoncli build/lnxmoncli.go

[ -f build/lnxmonsrv.go ] && rm build/lnxmonsrv.go
[ -f build/lnxmoncli.go ] && rm build/lnxmoncli.go

[ -d build/lib ] && rm -rf build/lib

printf "\n-- $(date) -- finished --\n"

date
