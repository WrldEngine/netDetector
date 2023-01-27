try:
    import os
    import socket
    import threading
    import sqlite3
    import datetime
    import requests
    import sys

except Exception as e:
    print('[!] Modules are not installed')

command_param = sys.argv[1]

db = sqlite3.connect('manage.db')
sql = db.cursor()

sql.execute("""CREATE TABLE IF NOT EXISTS devices(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ip TEXT,
    mac TEXT,
    device TEXT,
    date TEXT
)""")
db.commit()

my_local_ip = socket.gethostbyname(socket.gethostname())
print(f"Your local ip: {my_local_ip}")

dev_lst = []

def add_db_info(ip_addr, mac_addr, device_name, now_time):
    add_to_db = sql.execute(f"SELECT mac FROM devices WHERE mac = '{mac_addr}'")
    if add_to_db.fetchone() is None:
        sql.execute("INSERT INTO devices(ip, mac, date, device) VALUES(?, ?, ?, ?)", (ip_addr, mac_addr, now_time, device_name)); db.commit()
    else:
        sql.execute(f"UPDATE devices SET ip = '{ip_addr}', date = '{now_time}', device = '{device_name}' WHERE mac = '{mac_addr}'"); db.commit()

def get_device(mac):
    net_err = '{"errors":{"detail":"Not Found"}}'
    req_err = '{"errors":{"detail":"Too Many Requests","message":"Please slow down your requests or upgrade your plan at https://macvendors.com"}}'

    device = requests.get('https://api.macvendors.com/' + mac).text
    
    return "Not found" if device == net_err else device
    return "Req error" if device == req_err else device

def png(ip):
    arg = '-n' if os.name=='nt' else '-c'
    cmd = f'ping {arg} 1 {ip}'
    data = os.popen(cmd).readlines()
    for check in data:
        if 'ttl' in check.lower():    
            arp_comm = os.popen('arp -a').readlines()
            
            for arp_info in arp_comm:
                ip_dev_list = arp_info.split()

                if len(ip_dev_list) > 0 and ip_dev_list[0] == ip:
                    mac = ip_dev_list[1]
                    dev_names = data[1].split()
                    dev_name = dev_names[3]
            
                    inf = f"{ip} {mac}".split()
                    dev_lst.append(inf)
            break

if command_param == 'scan':
    start_ip = '192.168.1.0'.split('.')

    point = '.'
    end = '255'
    ip_range = ''

    start_ip_lst = start_ip[0] + point + start_ip[1] + point + start_ip[2] + point # 192.168.1.[number]


    if my_local_ip == '127.0.0.1':
        print("[!] Please check your internet connection !")

    else:
        lst_ip = [start_ip_lst + str(i) for i in range(int(end) - int(start_ip[3]))]
        try:
            lst_ip.remove(my_local_ip)
        except:
            print("[!] You are not on the local network")

        for host in lst_ip:
            flood = threading.Thread(target=png, args=[host]).start()

        for info in dev_lst:
            ip_addr, mac_addr = info[0], info[1]
            device_name = get_device(mac_addr)
            print(f"IP: {ip_addr:13} - {mac_addr} | {device_name}")

            now_time_mod = datetime.datetime.now()
            now_time = f"{now_time_mod.hour}:{now_time_mod.minute}:{now_time_mod.second} {now_time_mod.day}.{now_time_mod.month}.{now_time_mod.year}"

            add_db_info(ip_addr=ip_addr, mac_addr=mac_addr, device_name=device_name, now_time=now_time)

elif command_param == 'history':
    _output_db = sql.execute("SELECT * FROM devices ORDER BY id DESC")
    for out_db in _output_db:
        ip = out_db[1]
        mac, device_ip_mac = out_db[2], out_db[3]
        date = out_db[4]
        
        if len(device_ip_mac) > 40: device_ip_mac = device_ip_mac[:36] + '...'
    
        print(f"IP: {ip:13} - MAC: {mac} | {device_ip_mac} at {date}")

elif command_param == '--help' or '-h':
    print("Usage: bla bla bla...")
