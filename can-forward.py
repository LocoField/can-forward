import can
import threading
import queue
import pickle
import os

root_dir = os.path.dirname(os.path.abspath(__file__)) + '/'
pkl_filepath = root_dir + 'fwd.data'
log_filepath = root_dir + 'can1.log'

adp_data_dict = pickle.load(open(pkl_filepath, 'rb'))

can0 = can.interface.Bus(channel = 'can0', bustype = 'socketcan')
can1 = can.interface.Bus(channel = 'can1', bustype = 'socketcan')

can0_queue = queue.Queue()
can1_queue = queue.Queue()

def process_can0():
    while True:
        msg = can0.recv(0.1)
        if msg is None:
            continue

        can0_queue.put(msg)

        fwd = can1_queue.get()
        if fwd is None:
            continue

        can0.send(fwd)

def process_can1():
    while True:
        msg = can0_queue.get()
        if msg is None:
            continue

        for id in adp_data_dict:
            if msg.arbitration_id == id:
                msg = can.Message(
                    arbitration_id=id,
                    data=adp_data_dict[id],
                    timestamp=msg.timestamp,
                    is_extended_id=msg.is_extended_id,
                    is_remote_frame=msg.is_remote_frame,
                    is_error_frame=msg.is_error_frame,
                    channel=msg.channel,
                    dlc=msg.dlc,
                    is_fd=msg.is_fd,
                    is_rx=False,
                    bitrate_switch=msg.bitrate_switch,
                    error_state_indicator=msg.error_state_indicator,
                    check=False
                    )

        can1.send(msg)
        
        ack = can1.recv(0.1)
        if ack is None:
            continue

        can1_queue.put(ack)
        
        with open(log_filepath, 'wb') as log_file:
            log_file.write(f"{ack}\n")
            log_file.flush()

can0_thread = threading.Thread(target=process_can0)
can0_thread.start()

can1_thread = threading.Thread(target=process_can1)
can1_thread.start()

can0_thread.join()
can1_thread.join()

can0.shutdown()
can1.shutdown()
