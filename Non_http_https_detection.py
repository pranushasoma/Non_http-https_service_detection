#!/usr/bin/env python3

import sys
import csv
import urllib3
import requests
import subprocess
import time

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

REQUEST_TIMEOUT = (10, 10)

def append_entries(host, port, err_msg, status_code="N/A", header="N/A", comment="N/A", nikto_output="N/A"):
    with open("final_443_test_res.csv", 'a+', newline='') as file:
        append = csv.writer(file)
        rows = [[host, port, status_code, header, err_msg, comment, nikto_output]]
        append.writerows(rows)
        file.close()

def check_host(host, port):

    err_comment3 = 'http_error'
    err_comment5 = 'bad_status_line'
    err_comment6 = 'remote_disconnected'
    err_comment7 = 'connection_error'
    err_comment8 = 'Need more than 10 seconds to connect'
    err_comment9 = 'connect timeout'

    if title is False:
        import os
        for file in os.listdir(os.curdir):
            if "final_443_test_res.csv" == file:
                os.remove("final_443_test_res.csv")
        with open("final_443_test_res.csv", 'a+', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["IP", "Port", "Status_Code", "Header", "Error_Message", "comment", "Nikto_Output"])
        file.close()
    else:
        pass

    if int(port) not in [80, 443]:
        print(f'Invalid port({port}) for host: {host}')
        return

    proto = (port == 80) and 'http' or 'https'
    url = proto + '://' + host

    os_command = []
    if port == str(80):
        os_command = "nikto -host http://{} -findonly".format(host)
    elif port == str(443):
        os_command = "nikto -host https://{} -findonly".format(host)

    nikto_comm = subprocess.run(os_command, shell=True, stdout=subprocess.PIPE)
    count = 0
    while count < 30:
        if not nikto_comm:
            count = count + 5
            time.sleep(5)
        else:
            count = 30
    nikto_res = nikto_comm.stdout.split(b'\n')
    for ws in nikto_res:
        if "Server" in ws.decode("utf-8"):
            new_ws = (ws.split(b'\t')[1].decode("utf-8"))
            break
        else:
            curl_command = []
            if port == str(80):
                curl_command = "curl -I {}:80 | grep Server:" .format(host)
            elif port == str(443):
                curl_command = "curl -I -k {}:443 | grep Server:" .format(host)

            curl_comm = subprocess.run(curl_command, shell=True, stdout=subprocess.PIPE)
            while count < 30:
                if not curl_comm:
                    count = count + 5
                    time.sleep(5)
                else:
                    count = 30
            curl_res = curl_comm.stdout.split(b'\n')
            for ws in curl_res:
                if "Server" in ws.decode("utf-8"):
                    new_ws = (ws.split(b'\t')[0].decode("utf-8"))
                    break
            else:
                new_ws = "No web server found"
                break

    try:
        response = requests.get(url, verify=False, timeout=REQUEST_TIMEOUT)
        print(response.status_code)
        print(f'response.headers: {response.headers.get("Content-Type")}')
    except requests.exceptions.HTTPError as http_err:
        print(f'HTTPError:{host}:{port}:{http_err}')
        append_entries(host=host, port=port, status_code="N/A", header="N/A", err_msg=f"HTTPError:{host}:{port}:{http_err}", comment=err_comment3, nikto_output=new_ws)

    except requests.exceptions.SSLError as ssl_error:
        for error in ssl_error.args:
            for error in error.args:
                import re
                ssl_err_obj_list = error.split(',')
                for error in range(len(ssl_err_obj_list), 0, -1):
                    err_msg = re.sub('[^A-Za-z0-9]+', ' ', ssl_err_obj_list[error-1])
                    break
                append_entries(host=host, port=port, status_code="N/A", header="N/A",
                                err_msg="UnknownException: " + str(ssl_error), comment=err_msg, nikto_output=new_ws)
    except requests.exceptions.ConnectionError as con_error:
        str_err = str(con_error)
        if 'BadStatusLine' in str_err:
            print(f'BadStatusLine:{host}:{port}')
            append_entries(host=host, port=port, status_code="N/A", header="N/A", err_msg="BadStatusLine:" + str_err, comment=err_comment5, nikto_output=new_ws)
        elif 'RemoteDisconnected' in str_err:
            print(f'RemoteDisconnected:{host}:{port}')
            append_entries(host=host, port=port, status_code="N/A", header="N/A", err_msg="RemoteDisconnected:" + str_err, comment=err_comment6, nikto_output=new_ws)
        else:
            if err_comment9 in str_err:
                append_entries(host=host, port=port, status_code="N/A", header="N/A",
                               err_msg="ConnectionError: " + str_err, comment=err_comment8, nikto_output=new_ws)
            else:
                print(f'ConnectionError:{host}:{port}:{con_error}')
                append_entries(host=host, port=port, status_code="N/A", header="N/A", err_msg="ConnectionError: " + str_err, comment=err_comment7, nikto_output=new_ws)
    except Exception as err:
        print(f'UnknownException :: {err}')
        append_entries(host=host, port=port, status_code="N/A", header="N/A", err_msg="ConnectionError: " + str(err),
                       comment=err_comment8, nikto_output=new_ws)
    else:
        print(f'{proto.upper()}_{response.status_code}:{host}:{port}')
        append_entries(host=host, port=port, status_code=str(response.status_code),
                       header=str({response.headers.get("Content-Type")}), err_msg="N/A", comment="statuscode:" +str(response.status_code), nikto_output=new_ws)

#check_host(host="17.252.242.85", port=80)
title = True

if __name__ == "__main__":
    title = False
    with open(sys.argv[1], encoding='utf-8-sig') as f:
        for host in f.readlines():
            check_host(*host.strip().replace(',', ':').split(':'))
            count = 0
            while count < 30:
                if not host:
                    time.sleep(5)
                    count = count + 5
                else:
                    count = 30
            title = True