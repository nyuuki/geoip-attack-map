# start the Redis server if it isn't started already.
# $ redis-server
# default port is 6379
# make sure system can use a lot of memory and overcommit memory
REDIS_IP = '127.0.0.1'

WEBSOCK_PORT = 8888

# Look up service colors
SERVICE_RGB = {
    'FTP':'#ff0000',
    'SSH':'#ff8000',
    'TELNET':'#ffff00',
    'EMAIL':'#80ff00',
    'WHOIS':'#00ff00',
    'DNS':'#00ff80',
    'HTTP':'#00ffff',
    'HTTPS':'#0080ff',
    'SQL':'#0000ff',
    'SNMP':'#8000ff',
    'SMB':'#bf00ff',
    'AUTH':'#ff00ff',
    'RDP':'#ff0060',
    'DoS':'#ff0000',
    'ICMP':'#ffcccc',
    'OTHER':'#6600cc',
}

# required input paths
BLOCK_IP_LIST_FILE = 'block.txt'
# BLOCK_IP_LIST_FILE = '/mnt/map_attack_blk/LOG4.log'
