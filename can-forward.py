import can
import threading
import queue
import pickle
import os

root_dir = os.path.dirname(os.path.abspath(__file__)) + '/'
fwd_data_filepath = root_dir + 'fwd.data'
can0_log_filepath = root_dir + 'can0.log'
can1_log_filepath = root_dir + 'can1.log'

if os.path.exists(can0_log_filepath):
    os.remove(can0_log_filepath)

if os.path.exists(can1_log_filepath):
    os.remove(can1_log_filepath)

adp_data_dict = pickle.load(open(fwd_data_filepath, 'rb'))

can0 = can.interface.Bus(channel = 'can0', interface = 'socketcan')
can1 = can.interface.Bus(channel = 'can1', interface = 'socketcan')

can0_queue = queue.Queue()
can1_queue = queue.Queue()

def process_can0():
    while True:
        msg = can0.recv()
        if msg is not None:
            with open(can0_log_filepath, 'a') as log_file:
                can0_queue.put(msg)

                log_file.write(f"<< {msg}\n")
                log_file.flush()

        fwd = can1_queue.get()
        if fwd is not None:
            with open(can0_log_filepath, 'a') as log_file:
                can0.send(fwd)

                log_file.write(f">> {fwd}\n")
                log_file.flush()

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

        with open(can1_log_filepath, 'a') as log_file:
            can1.send(msg)

            log_file.write(f">> {msg}\n")
            log_file.flush()

            ack = can1.recv()
            if ack is not None:
                can1_queue.put(ack)

                log_file.write(f"<< {ack}\n")
                log_file.flush()

can0_thread = threading.Thread(target=process_can0)
can0_thread.start()

can1_thread = threading.Thread(target=process_can1)
can1_thread.start()

can0_thread.join()
can1_thread.join()

can0.shutdown()
can1.shutdown()
