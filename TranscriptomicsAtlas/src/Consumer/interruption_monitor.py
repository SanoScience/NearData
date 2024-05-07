import os
import signal
import threading
from time import sleep

import requests

from logger import logger


# TODO this is for spot, for slurm use https://stackoverflow.com/questions/44133636/slurm-access-walltime-limit-from-script
class SpotInterruptionMonitor(threading.Thread):
    _stopper: threading.Event
    url = 'http://169.254.169.254/latest/meta-data/spot/instance-action'

    def run(self):
        self._stopper = threading.Event()
        thread = threading.Thread(target=self.check_for_interruption)
        thread.start()

    def set_message(self, message):
        self.message = message

    def stop(self):
        self._stopper.set()

    def check_for_interruption(self):
        logger.info("[Monitor]: Started checking for interruptions")
        while not self._stopper.is_set():
            sleep(10)
            resp = requests.get(self.url)
            if resp.status_code != 404:
                resp = resp.json()
                if resp["action"] == 'stop' or resp["action"] == 'terminate':
                    logger.info(f"Received action: {resp['action']}.")  # TODO logger does not work with watchtower?
                    self.message.change_visibility(VisibilityTimeout=0)
                    logger.info(f"Message {self.message.body} returned to queue.")
                    os.kill(os.getpid(), signal.SIGTERM)
        logger.info(f"Monitor stopped.")

