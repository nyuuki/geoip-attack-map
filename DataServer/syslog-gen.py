#!/usr/bin/python3

# import random, syslog
import random
from const import PORTMAP, SYSLOG_PATH
from sys import exit
from time import sleep
import datetime


def main():
    port_list = []
    type_attack_list = []
    src_addr_list = ["203.0.113.1", "203.0.113.2", "11.11.11.11"]
    dst_addr_list = ["203.0.113.3", "203.0.113.4"]
    
    for port in PORTMAP:
        port_list.append(port)
        type_attack_list.append(PORTMAP[port])
    
    while True:
        port = random.choice(port_list)
        type_attack = random.choice(type_attack_list)
        cve_attack = 'CVE:{}:{}'.format(
                random.randrange(1, 2000),
                random.randrange(100, 1000))
        src_addr = random.choice(src_addr_list)
        dst_addr = random.choice(dst_addr_list)
        rand_data = '{},{},{},{},{},{}'.format(
                src_addr, dst_addr, port, port, type_attack, cve_attack)
        
        now = datetime.datetime.now()
        str_time = now.strftime('%H:%M:%S')
        str_month_name = now.strftime('%b')
        # Mar  3 19:32:23 ubuntu /syslog-gen.py:
        with open(SYSLOG_PATH, "a") as f:
            f.write("Mar  {2} {0} ubuntu {3}: {1}\n".format(
                    str_time, rand_data, now.day, str_month_name, __file__))
        # syslog.syslog(rand_data)
        print(rand_data)
        sleep(1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        exit()
