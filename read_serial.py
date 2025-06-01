import serial
import serial.tools.list_ports
import struct
import time
from multiprocessing import Process, Event, Value, Array


class ArduinoData:
    def __init__(self):
        # Try to reach arduino port
        self.port = 'COM6'#self._auto_port_sel()
        self.baudrate = 115200  

        if self.port is None:
            print("Port not found automatically. Quitting")
            return
        else:
            self.data = Array('d', range(2))
            self.stopEvent = Event()
            self.p = Process(target=self.aquire_data, args=[self.data, self.port, self.baudrate, self.stopEvent])

    def _auto_port_sel(self):
        # automatic port search
        print("Searching for ports...")
        portlist = serial.tools.list_ports.comports(include_links=False)
        print(f"Found following ports:\n")

        # take first port described as arduino
        auto_port = None
        for p in portlist:
            if 'Arduino' in p.description:
                auto_port = p.device
                print(f"Automatically selected port: {auto_port}")
        if auto_port is None:
            print("Arduino port not found.\nquitting....")
            return None
        else:
            return auto_port

    def start(self):
        self.p.start()

    def stop(self):
        self.stopEvent.set()
        self.p.join()

    def get(self):
        return self.data[:]

    def aquire_data(self, data, port, baudrate, stopEvent):
        # Start serial connection
        ser = serial.Serial(port=port, baudrate=baudrate)

        received_data = [0.0, 0.0]
        while not stopEvent.is_set():
            try:
                received_data = ser.read_until(expected=b'\r\n').strip().split(b';')
                # check if there is all data
                if len(received_data) == 2:
                    received_data = [float(i.decode('ansi')) for i in received_data]
                    # print(received_data)
                    data[:] = received_data
                else:
                    print("Received incorrect data.")
            except Exception as e:
                print(e)
                continue


if __name__ == '__main__':
    ardata = ArduinoData()
    ardata.start()
    while True:
    # for i in range(5):
        print(f"Eh: {ardata.get()}")
        # time.sleep(1)
    ardata.stop()
