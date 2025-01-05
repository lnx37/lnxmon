import argparse
import hashlib
import json
import logging
import logging.handlers
import math
import os
import re
import socket
import subprocess
import sys
import threading
import time
import traceback

try: from urllib.request import Request
except ImportError: from urllib2 import Request
try: from urllib.request import urlopen
except ImportError: from urllib2 import urlopen

SETTINGS = {
    'VERSION': '20220525',
    'DEBUG':   True,
    'API':     'http://127.0.0.1:1234/api',
    'PROJECT': 'DEFAULT',
    'TOKEN':   '123456',
}

logger = logging.getLogger()

def exec_cmd(cmd):
    try:
        popen = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        returncode = popen.wait()
        if returncode == 0:
            stdout_data = popen.communicate()[0]
            result = (returncode, stdout_data.decode('utf-8'))
        else:
            stderr_data = popen.communicate()[1]
            result = (returncode, stderr_data.decode('utf-8'))
    except KeyboardInterrupt:
        raise
    except:
        result = (1, traceback.format_exc())

    return result

def exec_cmd_with_timeout(cmd, timeout=10):
    try:
        is_timeout = False
        popen = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        begin_time = time.time()
        while True:
            returncode = popen.poll()
            if returncode is not None:
                break
            elapsed_time = time.time() - begin_time
            if elapsed_time > timeout:
                is_timeout = True
                popen.terminate()
                result = (1, 'command timed out after %d secs' % timeout)
        if is_timeout is False:
            if returncode == 0:
                stdout_data = popen.communicate()[0]
                result = (returncode, stdout_data.decode('utf-8'))
            else:
                stderr_data = popen.communicate()[1]
                result = (returncode, stderr_data.decode('utf-8'))
    except KeyboardInterrupt:
        raise
    except:
        result = (1, traceback.format_exc())

    return result

def http_post(api, data):
    begin_time = time.time()

    headers = {
        'Content-Type': 'application/json; charset=utf-8',
        'token': SETTINGS['TOKEN'],
    }
    data = data.encode('utf-8')
    request = Request(api, data=data, headers=headers)
    response = urlopen(request, timeout=30)
    try:
        code = response.code
        data = response.read()
    finally:
        response.close()

    logger.info('response code: %s' % code)
    logger.info('response body: %s' % data.decode('utf-8'))

    http_status_code = code

    elapsed_time = (time.time() - begin_time) * 1000
    logger.info('%s took %.6fms' % (api, elapsed_time))

    return http_status_code

def get_code():
    code = socket.gethostname().encode('utf-8')
    code = hashlib.md5(code).hexdigest()
    return code

def get_hostname():
    hostname = socket.gethostname()
    return hostname

def get_ip():
    cmd = 'ip -family inet address'
    result = exec_cmd_with_timeout(cmd)

    if result[0] != 0:
        logger.error("cmd: %s", cmd)
        logger.error("cmd result: %s", result)
        raise Exception(result)

    regexp = re.compile('inet\s*(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})')
    ips = regexp.findall(result[1])
    if '127.0.0.1' in ips:
        ips.remove('127.0.0.1')
    ip = ','.join(ips)

    return ip

def get_os_type():
    filename = '/etc/issue'
    if os.path.isfile('/etc/centos-release'):
        filename = '/etc/centos-release'
    elif os.path.isfile('/etc/redhat-release'):
        filename = '/etc/redhat-release'
    else:
        pass

    file = open(filename)
    try:
        os_type = file.readline().strip()
    finally:
        file.close()

    return os_type

def get_architecture():
    cmd = 'getconf LONG_BIT |head -c -1; echo -n "-bit "; uname -rm'
    result = exec_cmd_with_timeout(cmd)

    if result[0] != 0:
        logger.error("cmd: %s", cmd)
        logger.error("cmd result: %s", result)
        raise Exception(result)

    architecture = result[1].strip()

    return architecture

def get_cpu_processors():
    cpu_processors = 0

    file = open('/proc/cpuinfo')
    try:
        for line in file.readlines():
            if line.startswith('processor'):
                cpu_processors += 1
    finally:
        file.close()

    return cpu_processors

# https://www.kernel.org/doc/Documentation/filesystems/proc.txt
def get_mem_size():
    mem_size = 0

    file = open('/proc/meminfo')
    try:
        for line in file.readlines():
            if line.startswith('MemTotal:'):
                mem_size = int(line.split()[1])
                break
    finally:
        file.close()

    # GiB
    mem_size = int(round(float(mem_size) / (1024 * 1024)))

    return mem_size

# See get_disk_usage()
def get_disk_size():
    disk_size = 0

    file = open('/proc/mounts')
    try:
        for line in file.readlines():
            # /dev/loop0
            if (line.startswith('/dev') and
                '/dev/loop' not in line and
                'chroot' not in line and
                'docker' not in line):
                mount_point = line.split()[1]
                stat = os.statvfs(mount_point)
                disk_size += stat.f_frsize * stat.f_blocks
    finally:
        file.close()

    # GiB
    #
    # On Aliyun ECS
    # round() returns 39G
    # math.ceil() returns 40G
    disk_size = int(math.ceil(float(disk_size) / (1024 * 1024 * 1024)))

    return disk_size

def get_uptime():
    file = open('/proc/uptime')
    try:
        uptime = float(file.readline().split()[0])
    finally:
        file.close()

    # days
    uptime = round(uptime/(3600*24)*100) / 100

    return uptime

def get_loadavg():
    file = open('/proc/loadavg')
    try:
        fields = file.readline().split()
    finally:
        file.close()

    # 1m, 5m, 15m
    loadavg = '%s,%s,%s' % (fields[0], fields[1], fields[2])

    return loadavg

#  1: user
#  2: nice
#  3: system
#  4: idle
#  5: iowait
#  6: irq
#  7: softirq
#  8: steal
#  9: guest
# 10: guest_nice
#
# https://www.kernel.org/doc/Documentation/filesystems/proc.txt
def get_cpu_usage():
    def calculate_cpu_usage():
        file = open('/proc/stat')
        try:
            fields = file.readline().split()
            user = int(fields[1])
            nice = int(fields[2])
            system = int(fields[3])
            idle = int(fields[4])
            iowait = int(fields[5])
            irq = int(fields[6])
            softirq = int(fields[7])
        finally:
            file.close()

        used = user + nice + system
        total = user + nice + system + idle + iowait + irq + softirq

        return used, iowait, total

    used, iowait, total = calculate_cpu_usage()
    time.sleep(1)
    used2, iowait2, total2 = calculate_cpu_usage()

    cpu_used = float(used2-used) / float(total2-total)
    cpu_iowait = float(iowait2-iowait) / float(total2-total)

    cpu_usage = '%.2f,%.2f' % (cpu_used*100, cpu_iowait*100)

    return cpu_usage

# https://www.kernel.org/doc/Documentation/filesystems/proc.txt
def get_mem_usage():
    file = open('/proc/meminfo')
    try:
        for line in file.readlines():
            if line.startswith('MemTotal:'):
                mem_total = int(line.split()[1])
            elif line.startswith('MemFree:'):
                mem_free = int(line.split()[1])
            elif line.startswith('Buffers:'):
                buffers = int(line.split()[1])
            elif line.startswith('Cached:'):
                cached = int(line.split()[1])
            elif line.startswith('SwapTotal:'):
                swap_total = int(line.split()[1])
            elif line.startswith('SwapFree:'):
                swap_free = int(line.split()[1])
    finally:
        file.close()

    # GiB
    mem_total2 = int(round(float(mem_total) / (1024 * 1024)))
    swap_total2 = int(round(float(swap_total) / (1024 * 1024)))

    mem_used = float(mem_total-mem_free-buffers-cached) / float(mem_total) * 100
    swap_used = float(swap_total-swap_free) / (float(swap_total) + 0.1) * 100

    mem_usage = '%.0f,%.2f,%.0f,%.2f' % (mem_total2, mem_used, swap_total2, swap_used)

    return mem_usage

# struct statvfs {
#     unsigned long  f_bsize;    /* Filesystem block size */
#     unsigned long  f_frsize;   /* Fragment size */
#     fsblkcnt_t     f_blocks;   /* Size of fs in f_frsize units */
#     fsblkcnt_t     f_bfree;    /* Number of free blocks */
#     fsblkcnt_t     f_bavail;   /* Number of free blocks for unprivileged users */
#     fsfilcnt_t     f_files;    /* Number of inodes */
#     fsfilcnt_t     f_ffree;    /* Number of free inodes */
#     fsfilcnt_t     f_favail;   /* Number of free inodes for unprivileged users */
#     unsigned long  f_fsid;     /* Filesystem ID */
#     unsigned long  f_flag;     /* Mount flags */
#     unsigned long  f_namemax;  /* Maximum filename length */
# };
#
# unsigned long f_bsize    File system block size.
# unsigned long f_frsize   Fundamental file system block size.
# fsblkcnt_t    f_blocks   Total number of blocks on file system in units of f_frsize.
# fsblkcnt_t    f_bfree    Total number of free blocks.
# fsblkcnt_t    f_bavail   Number of free blocks available to non-privileged process.
# fsfilcnt_t    f_files    Total number of file serial numbers.
# fsfilcnt_t    f_ffree    Total number of free file serial numbers.
# fsfilcnt_t    f_favail   Number of file serial numbers available to non-privileged process.
# unsigned long f_fsid     File system ID.
# unsigned long f_flag     Bit mask of f_flag values.
# unsigned long f_namemax  Maximum filename length.
#
# statvfs.f_frsize * statvfs.f_blocks     # Size of filesystem in bytes
# statvfs.f_frsize * statvfs.f_bfree      # Actual number of free bytes
# statvfs.f_frsize * statvfs.f_bavail     # Number of free bytes that ordinary users are allowed to use (excl. reserved space)
#
# https://man7.org/linux/man-pages/man3/statvfs.3.html
# https://docs.python.org/2/library/os.html#os.statvfs
# https://docs.python.org/3/library/os.html#os.statvfs
# https://stackoverflow.com/questions/4260116/find-size-and-free-space-of-the-filesystem-containing-a-given-file
def get_disk_usage():
    disks = []

    file = open('/proc/mounts')
    try:
        for line in file.readlines():
            # /dev/loop0
            if (line.startswith('/dev') and
                '/dev/loop' not in line and
                'chroot' not in line and
                'docker' not in line):
                mount_point = line.split()[1]

                stat = os.statvfs(mount_point)

                # GiB
                disk_total = int(round(float(stat.f_frsize*stat.f_blocks) / (1024 * 1024 * 1024)))
                disk_used = float(stat.f_frsize*(stat.f_blocks-stat.f_bfree)) / float(stat.f_frsize*stat.f_blocks) * 100

                inode_used = 0
                if stat.f_files != 0:
                    inode_used = float(stat.f_files-stat.f_ffree) / float(stat.f_files) * 100

                disk = '%s_%.0f_%.2f_%.2f' % (mount_point, disk_total, disk_used, inode_used)

                disks.append(disk)
    finally:
        file.close()

    disk_usage = ','.join(disks)

    return disk_usage

#  0: major number
#  1: minor mumber
#  2: device name
#  3: reads completed successfully
#  4: reads merged
#  5: sectors read
#  6: time spent reading (ms)
#  7: writes completed
#  8: writes merged
#  9: sectors written
# 10: time spent writing (ms)
# 11: I/Os currently in progress
# 12: time spent doing I/Os (ms)
# 13: weighted time spent doing I/Os (ms)
#
# https://www.kernel.org/doc/Documentation/iostats.txt
# https://www.kernel.org/doc/Documentation/ABI/testing/procfs-diskstats
def get_disk_io_rate():
    def calculate_disk_io_rate(regexp):
        rsectors = 0
        wsectors = 0
        current_ios = 0

        file = open('/proc/diskstats')
        try:
            for line in file.readlines():
                if regexp.search(line) is not None:
                    fields = line.split()
                    rsectors += int(fields[5])
                    wsectors += int(fields[9])
                    current_ios += int(fields[11])
        finally:
            file.close()

        return rsectors, wsectors, current_ios

    regexp = None
    file = open('/proc/diskstats')
    try:
        is_matched = False
        for line in file.readlines():
            patterns = [
                ' sd[a-z] ',
                ' sd[a-z][0-9] ',
                ' vd[a-z] ',
                ' vd[a-z][0-9] ',
                ' xvd[a-z] ',
                ' xvd[a-z][0-9] ',
                ' hd[a-z] ',
                ' hd[a-z][0-9] ',
            ]
            for pattern in patterns:
                regexp = re.compile(pattern)
                if regexp.search(line) is not None:
                    is_matched = True
                    break
            if is_matched is True:
                break
    finally:
        file.close()

    rsectors, wsectors, _ = calculate_disk_io_rate(regexp)
    time.sleep(1)
    rsectors2, wsectors2, current_ios = calculate_disk_io_rate(regexp)

    # KiB/s
    read_rate = float(rsectors2-rsectors) * 512 / 1024
    write_rate = float(wsectors2-wsectors) * 512 / 1024

    disk_io_rate = '%.2f,%.2f,%d' % (read_rate, write_rate, current_ios)

    return disk_io_rate

#  0: Interface
#  1: Receive bytes
#  2: Receive packets
#  3: Receive errs
#  4: Receive drop
#  5: Receive fifo
#  6: Receive frame
#  7: Receive compressed
#  8: Receive multicast
#  9: Transmit bytes
# 10: Transmit packets
# 11: Transmit errs
# 12: Transmit drop
# 13: Transmit fifo
# 14: Transmit frame
# 15: Transmit compressed
# 16: Transmit multicast
#
# https://www.kernel.org/doc/Documentation/filesystems/proc.txt
def get_nic_io_rate():
    def calculate_nic_io_rate():
        receive_bytes = 0
        transmit_bytes = 0
        receive_packets = 0
        transmit_packets = 0

        file = open('/proc/net/dev')
        try:
            for line in file.readlines():
                if ('Inter' not in line and
                    'face' not in line and
                    'lo:' not in line):
                    fields = line.split()
                    receive_bytes += int(fields[1])
                    receive_packets += int(fields[2])
                    transmit_bytes += int(fields[9])
                    transmit_packets += int(fields[10])
        finally:
            file.close()

        return receive_bytes, transmit_bytes, receive_packets, transmit_packets

    receive_bytes, transmit_bytes, receive_packets, transmit_packets = calculate_nic_io_rate()
    time.sleep(1)
    receive_bytes2, transmit_bytes2, receive_packets2, transmit_packets2 = calculate_nic_io_rate()

    # KiB/s
    receive_bytes_rate = float(receive_bytes2-receive_bytes) / 1024
    receive_packets_rate = receive_packets2 - receive_packets
    transmit_bytes_rate = float(transmit_bytes2-transmit_bytes) / 1024
    transmit_packets_rate = transmit_packets2 - transmit_packets

    nic_io_rate = '%.2f,%s,%.2f,%s' % (receive_bytes_rate, receive_packets_rate, transmit_bytes_rate, transmit_packets_rate)

    return nic_io_rate

def get_tcp_sockets():
    inuse = 0
    tw = 0

    file = open('/proc/net/sockstat')
    try:
        for line in file.readlines():
            if line.startswith('TCP:'):
                fields = line.split()
                inuse += int(fields[2])
                tw += int(fields[6])
    finally:
        file.close()

    if os.path.exists('/proc/net/sockstat6'):
        file = open('/proc/net/sockstat6')
        try:
            for line in file.readlines():
                if line.startswith('TCP6:'):
                    fields = line.split()
                    inuse += int(fields[2])
        finally:
            file.close()

    tcp_sockets = '%d,%d' % (inuse, tw)

    return tcp_sockets

def get_users():
    cmd = 'users'
    result = exec_cmd_with_timeout(cmd)

    if result[0] != 0:
        logger.error("cmd: %s", cmd)
        logger.error("cmd result: %s", result)
        raise Exception(result)

    users = len(result[1].split())

    return users

def get_current_time():
    current_time = time.strftime('%Y-%m-%d %H:%M:%S')
    return current_time

def get_host():
    host = {
        'code':           get_code(),
        'hostname':       get_hostname(),
        'ip':             get_ip(),
        'os_type':        get_os_type(),
        'architecture':   get_architecture(),
        'cpu_processors': get_cpu_processors(),
        'mem_size':       get_mem_size(),
        'disk_size':      get_disk_size(),
        'uptime':         get_uptime(),
        'heartbeat_time': get_current_time(),
        'project':        SETTINGS['PROJECT'],
        'version':        SETTINGS['VERSION'],
    }

    if SETTINGS['DEBUG'] is True:
        logger.info('host: \n' + json.dumps(host, indent=4))

    host = json.dumps(host)

    return host

def get_host_metric():
    host_metric = {
        'code':           get_code(),
        'hostname':       get_hostname(),
        'ip':             get_ip(),
        'loadavg':        get_loadavg(),
        'cpu_usage':      get_cpu_usage(),
        'mem_usage':      get_mem_usage(),
        'disk_usage':     get_disk_usage(),
        'disk_io_rate':   get_disk_io_rate(),
        'nic_io_rate':    get_nic_io_rate(),
        'tcp_sockets':    get_tcp_sockets(),
        'users':          get_users(),
        'heartbeat_time': get_current_time(),
        'project':        SETTINGS['PROJECT'],
    }

    if SETTINGS['DEBUG'] is True:
        logger.info('host_metric: \n' + json.dumps(host_metric, indent=4))

    host_metric = json.dumps(host_metric)

    return host_metric

def report_host():
    while True:
        try:
            api = '%s/report_host' % SETTINGS['API']
            host = get_host()
            logger.info('api: %s' % api)
            logger.info('host: %s' % host)
            http_post(api, host)
        except:
            logger.error(traceback.format_exc())

        if SETTINGS['DEBUG'] is True:
            time.sleep(5 * 1)
        else:
            time.sleep(5 * 60)

def report_host_metric():
    while True:
        try:
            api = '%s/report_host_metric' % SETTINGS['API']
            host_metric = get_host_metric()
            logger.info('api: %s' % api)
            logger.info('host_metric: %s' % host_metric)
            http_post(api, host_metric)
        except:
            logger.error(traceback.format_exc())

        if SETTINGS['DEBUG'] is True:
            time.sleep(1 * 1)
        else:
            time.sleep(1 * 60)

if __name__ == '__main__':
    logger.setLevel(logging.INFO)
    fmt = '%(asctime)s,%(msecs)03d [%(name)s:%(funcName)s:%(lineno)d] %(levelname)-5s - %(message)s'
    formatter = logging.Formatter(fmt=fmt, datefmt='%Y-%m-%d %H:%M:%S')
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    parser = argparse.ArgumentParser()
    parser.add_argument('--host', type=str, default='127.0.0.1', help='Host')
    parser.add_argument('--port', type=int, default=1234, help='Post')
    parser.add_argument('--project', type=str, default='DEFAULT', help='Project')
    parser.add_argument('--debug', action='store_true', default=False, help='Debug')
    args = parser.parse_args()

    logger.info(args)

    logger.info('host: %s' % args.host)
    logger.info('port: %s' % args.port)
    logger.info('project: %s' % args.project)
    logger.info('debug: %s' % args.debug)

    SETTINGS['API'] = 'http://%s:%d/api' % (args.host, args.port)
    SETTINGS['PROJECT'] = args.project
    SETTINGS['DEBUG'] = args.debug

    logger.info("SETTINGS: %s", SETTINGS)

    thread_report_host = threading.Thread(target=report_host)
    thread_report_host.daemon = True
    thread_report_host.start()

    thread_report_host_metric = threading.Thread(target=report_host_metric)
    thread_report_host_metric.daemon = True
    thread_report_host_metric.start()

    while thread_report_host.is_alive() or thread_report_host_metric.is_alive():
        time.sleep(1)
