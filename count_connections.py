import subprocess

import psutil


def strip_string(string):
    string = str(string).replace('b', '').replace("'", '').replace('"', '').replace('\\n', '').replace('\\r', '')
    return string.strip()

def count_max_connections(os='windows'):
    if os == 'windows':
        sockets = int(subprocess.check_output('netstat -an | find /C /I "tcp"', shell=True))
        file_descriptors = len(psutil.Process().open_files())
        return max(sockets, file_descriptors)
    elif os == 'linux':
        sockets = subprocess.check_output('netstat -an | grep :80 | wc -l', shell=True)
        ulimit_output = subprocess.check_output('ulimit -n', shell=True)
        sockets = int(strip_string(sockets))
        file_descriptors = int(ulimit_output.strip())
        return max(sockets, file_descriptors)

def count_current_connections(os='windows'):
    if os == 'windows':
        sockets = psutil.net_connections(kind='inet')
        sockets = [s.laddr for s in sockets]
        connections = psutil.net_connections()
        return len(sockets), len(connections)
    elif os == 'linux':
        sockets = int(subprocess.check_output('netstat -an | grep :80 | wc -l', shell=True))
        return sockets