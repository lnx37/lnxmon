#!/bin/bash

set -e
set -o pipefail
set -u
set -x

cd "$(dirname "$0")"

date

# go-sqlite3
if [ ! -f lib/go-sqlite3-1.14.16.tar.gz ]; then
  if ! (tar tvf lib/go-sqlite3-1.14.16.tar.gz >/dev/null 2>&1); then
    wget -c "https://github.com/mattn/go-sqlite3/archive/refs/tags/v1.14.16.tar.gz" -O lib/go-sqlite3-1.14.16.tar.gz
  fi
fi

# pure css
# https://purecss.io/
if [ ! -f static/pure-min.css ]; then
  wget -c "https://cdn.jsdelivr.net/npm/purecss@3.0.0/build/pure-min.css" -O static/pure-min.css
fi

# pure css grids
# https://purecss.io/grids/
if [ ! -f static/grids-responsive-min.css ]; then
  wget -c "https://cdn.jsdelivr.net/npm/purecss@3.0.0/build/grids-responsive-min.css" -O static/grids-responsive-min.css
fi

# echarts
# https://echarts.apache.org/en/builder.html
# https://github.com/apache/echarts/tree/5.4.3/dist
# https://github.com/apache/echarts/blob/5.4.3/dist/echarts.min.js
# https://echarts.apache.org/en/builder/echarts.html?charts=line&components=gridSimple,title,legendScroll,tooltip,markLine&api=true&version=5.4.3

date
