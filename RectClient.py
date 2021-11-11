#!/usr/bin/env python3

import socket
from enum import Enum, IntEnum
import logging
import json
from typing import Tuple
from datetime import timedelta
from datetime import datetime

HOST_NAME = 'RectTestServer'

class GpioDirection(str, Enum):
    INPUT = 'input',
    OUTPUT = 'output'

class GpioOutputState(IntEnum):
    LOW = 0,
    HIGH = 1

class GpioPullup(IntEnum):
    DISABLED = 0,
    ENABLED = 1

class UartSpeed(str, Enum):
    SPEED_9600 = '9k',
    SPEED_38400 = '38k',
    SPEED_115200 = '115k',

class UartParity(str, Enum):
    DISABLED = 'disabled',
    EVEN = 'even',
    ODD = 'odd'

class UartStopBit(IntEnum):
    ONE_STOP_BIT = 1
    TWO_STOP_BIT = 2

class UartDataSize(IntEnum):
    FIVE_BIT = 5
    SIX_BIT = 6
    SEVEN_BIT = 7
    EIGHT_BIT = 8

class SpiSpeedLevel(IntEnum):
    SPEED_8MBIT_SEC = 0
    SPEED_4MBIT_SEC = 1
    SPEED_2MBIT_SEC = 2

class SpiMsbLsb(str, Enum):
    MSB = 'msb'
    LSB = 'lsb'

class SpiSampleMode(str, Enum):
    LEADING_RISING = 'lr',
    TRAILING_FALLING = 'tf',
    LEADING_FALLING = 'lf',
    TRAILING_RISING = 'tr'

class I2cReadWrite(str, Enum):
    READ = 'read',
    WRITE = 'write'

class I2cSpeedLevel(IntEnum):
    SPEED_100K = 1
    SPEED_200K = 2
    SPEED_300K = 3
    SPEED_400K = 4

class AdcReference(str, Enum):
    REF_5V = '5v',
    REF_2V56 = '2.56v'
    REF_1V1 = '1.1v'

class PwmDisEnable(str, Enum):
    ENABLE = 'enabled',
    DISABLE = 'disabled'

class PwmTimeUnit(str, Enum):
    MILLI_SEC = 'ms'
    MICRO_SEC = 'us'

class ReadWrite(str, Enum):
    READ = 'read'
    WRITE = 'write'

class EventType(str, Enum):
    NOW_EVENT = 'now',
    SCHEDULE_EVENT = 'schedule',
    PIN_STATE_EVENT = 'pinstate'

class PinStateEventTrigger(str, Enum):
    CHANGE = 'change',
    FALLING = 'falling',
    RISING = 'rising'

class BaseRequest:
    def __init__(self, event: str, request: object, return_val : [str] = None):
        self.request = request
        self.request['event'] = event
        self.actions = []
        self.return_val = return_val

    def GetActions(self) -> [[str]]:
        return self.actions

    def GetReturnVal(self) -> [str]:
        return self.return_val

    def AddAction(self, action: [str]) -> None:
        self.actions.append(action)

    def CreateRequest(self) -> object:
        self.request['actions'] = BaseRequest.GetActions(self)
        if BaseRequest.GetReturnVal(self):
            self.request['return'] = BaseRequest.GetReturnVal(self)
        return self.request

    def CreatePayload(self) -> str:
        self.request['actions'] = BaseRequest.GetActions(self)
        if BaseRequest.GetReturnVal(self):
            self.request['return'] = BaseRequest.GetReturnVal(self)
        return json.dumps(self.request)

class NowEventRequest(BaseRequest):
    def __init__(self, return_val: [str] = None):
        self.request = {}
        BaseRequest.__init__(self, 'now', self.request, return_val)

class ScheduleEventRequest(BaseRequest):
    def __init__(self, interval: timedelta = None, start_datetime: datetime = None, end_datetime: datetime = None, return_val: [str] = None):
        self.request = {}
        super('schedule', self.request, return_val)
        self.start = None
        self.end = None
        if (not interval) and (not start_datetime) and (not end_datetime):
            raise ValueError('One of interval or start_datetime or end_datetime need to be non-empty')
        if interval:
            interval_sec = interval.total_seconds()
            if interval_sec > 7 * 24 * 60 * 60:  # maximum interval limits to 7 days
                raise ValueError('Cannot support intervanl more than 7 days')
            elif interval_sec > 24 * 60 * 60:
                self.request['interval'] = f'{int(interval.total_seconds() / 24 * 60 * 60)}d'
            elif interval_sec > 60 * 60:
                self.request['interval'] = f'{int(interval.total_seconds() / 60 * 60)}h'
            elif interval_sec > 60:
                self.request['interval'] = f'{int(interval.total_seconds() / 60)}m'
            else:
                self.request['interval'] = f'{int(interval.total_seconds())}s'

        if start_datetime:
            self.request['start'] = start_datetime.strftime('%Y/%m/%d %H/%M/%S')

        if end_datetime:
            self.request['end'] = end_datetime.strftime('%Y/%m/%d %H/%M/%S')

class PinStateEventRequest(BaseRequest):
    def __init__(self, pin: int, trigger: PinStateEventTrigger, return_val: [str] = None):
        self.request = {}
        super('pinstate', self.request, return_val)
        self.request['pin'] = pin
        self.request['trigger'] = trigger

class ReturnBuilder():

    @staticmethod
    def TcpReturn(ip_addr: bytearray, port: int) -> [str]:
        tcp_str = ''
        for val in (ip_addr)[:-1]:
            tcp_str += str(val)
            tcp_str += '.'
        tcp_str += str((ip_addr[-1]))
        tcp_str += ':' + str(port)
        return ['tcp', tcp_str]

    @staticmethod
    def UdpReturn(ip_addr: bytearray, port: int) -> [str]:
        udp_str = ''
        for val in (ip_addr)[:-1]:
            udp_str += str(val)
            udp_str += '.'
        udp_str += str((ip_addr[-1]))
        udp_str += ':' + str(port)
        return ['udp', udp_str]

    @staticmethod
    def FileReturn(file_name: str) -> [str]:
        return ['file', file_name]

class ActionBuilder():

    @staticmethod
    def GpioAction(pin_id: int, direction: GpioDirection, value: GpioOutputState or GpioPullup) -> [str]:

        if (direction == GpioDirection.OUTPUT and isinstance(value, GpioOutputState)) or        \
            (direction == GpioDirection.INPUT and isinstance(value, GpioPullup)):
            action = ['gpio', pin_id, direction, value]
        else:
            raise ValueError('gpio output state need specify')
        return action
        #return self.__send_request('POST', '/hardware/operation',  json.dumps(action))

    @staticmethod
    def UartAction(uart_id: int, speed_selection: UartSpeed, parity: UartParity, stop_bit: UartStopBit, data_size: UartDataSize,
                            receive_timeout: int, receive_data_len: int, send_data_len: int, data: bytearray) -> [str]:
        action = ['uart', uart_id, speed_selection, parity, stop_bit, data_size, receive_timeout, receive_data_len, send_data_len, data]
        return action

    @staticmethod
    def SpiAction(spi_index: int, speed_level: SpiSpeedLevel, cs_pin: int, sample_mode: SpiSampleMode,
                            msb_lsb: SpiMsbLsb, receive_length: int, send_length: int, data: bytearray) -> [str]:
        action = ['spi', spi_index, speed_level, cs_pin, sample_mode, msb_lsb, receive_data_len, send_data_len, data]
        return action

    @staticmethod
    def I2cAction(i2c_index: int, operation: I2cReadWrite, device_addr:int, register_addr: int, length: int, data: bytearray) -> [str]:
        if operation == I2cReadWrite.READ:
            action = ['i2c', 0, 'read', I2cSpeedLevel, device_addr, register_addr, length]
        else:
            action = ['i2c', 0, 'write', I2cSpeedLevel, device_addr, register_addr, length, data]
        return action

    @staticmethod
    def AdcAction(channel_id: int, reference: AdcReference) -> [str]:
        action = ['adc', channel_id, reference]
        return action

    @staticmethod
    def PwmActionEnable(timer_index: int, time_unit: PwmTimeUnit, period: int, duty_cycle_a: int,
            duty_cycle_b: int, duty_cycle_c: int, duration_in_10ms: int) -> [str]:
        action = ['pwm', timer_index, 'enabled', time_unit, period, duty_cycle_a, duty_cycle_b, duty_cycle_c, duration_in_10ms]
        return action

    @staticmethod
    def PwmActionDisable(timer_index: int) -> [str]:
        action = ['pwm', timer_index, 'disabled']
        return action

    @staticmethod
    def FileActionRead(file_name: str) -> [str]:
        action = ['file', 0, ReadWrite.READ, file_name]
        return action

    @staticmethod
    def FileActionWrite(file_name: str, content: str) -> [str]:
        action = ['file', 0, ReadWrite.WRITE, content]
        return action

    @staticmethod
    def RtcActionRead() -> [str]:
        action = ['rtc', 0, 'read']
        return action

    @staticmethod
    def RtcActionWrite(year: int, month: int, date: int, hour: int, minute: int, second: int) -> [str]:
        action = ['rtc', 0, 'write', year, month, date, hour, minute, second]
        return action

class RectClient:
    def __init__(self, use_dhcp = False, target_ip = None, target_mdns_name = None):

        if target_ip:
            self.target_ip = target_ip
            self.target_port = 80

    def __SendRequest(self, method: str, uri: str, payload: str = None) -> Tuple[str, str]:
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
        finally:
            client.close()

        # only split once
        header, payload = data.split(b'\r\n\r\n', 1)
        return header, payload

    def __GetPage(self, uri: str) -> Tuple[str, str]:
        return self.__SendRequest('GET', '/', None)

    def GetIndexPage(self) -> str:
        header, payload = self.__GetPage('/')
        return payload

    def GetPage(self, uri: str) -> str:
        header, payload = self.__GetPage(uri)
        return payload

    def SendHardwareOperationRequest(self, payload) -> object:
       header, payload = self.__SendRequest('POST', '/hardware/operation', payload)
       return json.loads(payload)


if __name__ == "__main__":
    client = RectClient(target_ip = '10.0.0.100')

    return_val = ReturnBuilder.TcpReturn(bytearray([192,168,1,1]), 5000)
    now_request = NowEventRequest(return_val)
    gpio_action = ActionBuilder.GpioAction(0, GpioDirection.OUTPUT, GpioOutputState.HIGH)
    now_request.AddAction(gpio_action)
    gpio_action = ActionBuilder.GpioAction(1, GpioDirection.INPUT, GpioPullup.ENABLED)
    now_request.AddAction(gpio_action)
    payload = now_request.CreatePayload()
    reply = client.SendHardwareOperationRequest(payload)
    print(reply)




