import os
import logging
from datetime import datetime
import psutil
import time

LOG_FILE = 'bandwidth.log'

def setup_logging():
    logging.basicConfig(
        filename=LOG_FILE,
        level=logging.INFO,
        format="%(asctime)s %(message)s",
        datefmt="%Y-%m-%d %H:%M",
    )

def save_logging():
    setup_logging()
    try:
        nowTime = datetime.now().replace(microsecond=0)
        lastTime = datetime.strftime(nowTime, '%Y-%m-%d %H:%M:%S')
        # print("lastTime", lastTime)
        upload=psutil.net_io_counters(pernic=True)['Ethernet'].bytes_sent
        download=psutil.net_io_counters(pernic=True)['Ethernet'].bytes_recv
        up_down=(upload,download)
        # print(up_down)
        time.sleep(150)
        upload1=psutil.net_io_counters(pernic=True)['Ethernet'].bytes_sent
        download1=psutil.net_io_counters(pernic=True)['Ethernet'].bytes_recv
        up_down1=(upload1,download1)
        # print(up_down1)
        upload_bw = round((upload1-upload) / 1024, 2)
        download_bw = round((download1-download) / 1024, 2)
        print("UL: {:0.2f} kB".format(upload_bw), "DL: {:0.2f} kB".format(download_bw))
    except ValueError as err:
        logging.info(err)
    else:
        logging.info("%5.1f %5.1f", upload_bw, download_bw)

if __name__ == "__main__":
    while True:
        save_logging()