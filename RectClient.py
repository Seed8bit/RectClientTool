#!/usr/bin/env python3

import socket
from enum import Enum, IntEnum
import logging
import json
from typing import Tuple

HOST_NAME = 'RectTestServer'

class BaseRequest:
    pass

class NowEventRequest(BaseRequest):
    pass

class ScheduleEventRequest(BaseRequest):
    pass

class PinStateEventRequest(BaseRequest):
    pass

class ActionConstructor():
    pass

class RectClient:
    def __init__(self, use_dhcp = False, target_ip = None, target_mdns_name = None):

        if target_ip:
            self.target_ip = target_ip
            self.target_port = 80

    def __send_request(self, method: str, uri: str, payload: str = None) -> Tuple[str, str]:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # connect to the server
        client.connect((self.target_ip, self.target_port))

        if payload:
            request = f'{method} {uri} HTTP/1.1\r\nHost: {HOST_NAME}\r\n'  \
                      f'Content-Length:{len(payload)}\r\n\r\n'
            request += payload
        else:
            request = f'{method} {uri} HTTP/1.1\r\nHost: {HOST_NAME}\r\n\r\n'

        client.send(request.encode())

        try:
            data = client.recv(4096)

            while True:
                more = client.recv(4096)
                if not more:
                    break
                else:
                    data += more
        except socket.timeout:
            err_msg = "socket time out"
            logging.error(f'HTTP request error: {err_msg}')
            raise Exception

        # only split once
        header, payload = data.split(b'\r\n\r\n', 1)
        return header, payload

    def __GetPage(self, uri: str) -> Tuple[str, str]:
        return self.__send_request('GET', '/', None)

    def GetIndexPage(self) -> str:
        header, payload = self.__GetPage('/')
        return payload

    def GetPage(self, uri: str) -> str:
        header, payload = self.__GetPage(uri)
        return payload

    def ConstructGpioAction(self, pin_id: int, state, value) -> [str]:

        action = {
            'event': 'now',
            'actions': [['gpio', 0, 'output', 0]]
        }
        return self.__send_request('POST', '/hardware/operation',  json.dumps(action))

    def ConstructUartAction(self):
        pass

    def ConstructSpiAction(self):
        pass

    def ConstructI2cAction(self):
        pass

    def ConstructAdcAction(self):
        pass

    def ConstructPwmAction(self):
        pass

    def ConstructInterruptAction(self):
        pass

    def ConstructFileAction(self):
        pass

    def ConstructRtcAction(self):
        pass

if __name__ == "__main__":
    client = RectClient(target_ip = '10.0.0.100')
    #index_page = client.GetIndexPage()
    header, payload = client.ConstructGpioAction(0, 0, 0)
    print(payload)




