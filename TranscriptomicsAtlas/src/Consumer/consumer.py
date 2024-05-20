import os
import time

import boto3
import requests

if os.environ["execution_mode"] == "EC2":
    os.environ['AWS_DEFAULT_REGION'] = requests.get('http://169.254.169.254/latest/meta-data/placement/region').text

from aws_utils import terminate_itself_in_asg
from interruption_monitor import SpotInterruptionMonitor
from config import nproc, INTERRUPTION_MONITORING, PIPELINE_TYPE, EXECUTION_MODE
from logger import logger
from pipeline import Pipeline
from salmon_pipeline import SalmonPipeline
from STAR_pipeline import STARPipeline
from utils import PipelineError

logger.info(f"Nproc={nproc}")


def process_message_ec2(pipeline_class, message):
    try:
        pipeline = pipeline_class(message.body)

        if INTERRUPTION_MONITORING == "True":
            monitor = SpotInterruptionMonitor()
            logger.info("Starting interruption monitor.")
            monitor.set_message(message)
            monitor.run()

        if pipeline.check_if_file_already_processed():
            message.delete()
            return

        try:
            pipeline.start()
        except PipelineError as e:
            logger.warning(e)
            pipeline.metadata["error_type"] = e.error_type

        pipeline.gather_metadata()
        pipeline.upload_metadata()
        pipeline.clean()

        message.delete()

        if INTERRUPTION_MONITORING == "True":
            logger.info("Stopping interruption monitor.")
            monitor.stop()

        logger.info("Processed and deleted msg. Awaiting next one")

    except Exception as e:
        message.delete()   # todo move to dead letter queue
        logger.warning(f"Terminating instance due to error {e} with message {message.body}")
        terminate_itself_in_asg(decrease_capacity=False)


def process_message_hpc(pipeline_class, message):
    try:
        pipeline = pipeline_class(message.body)
        logger.info(f"Received msg={message.body}")

        if pipeline.check_if_file_already_processed():
            message.delete()
            return

        try:
            if PIPELINE_TYPE == "prefetch":
                pipeline.prefetch_only()
            elif PIPELINE_TYPE == "fasterq-dump":
                pipeline.fasterq_dump_only()
            else:
                pipeline.alignment()

        except PipelineError as e:
            logger.warning(e)
            pipeline.metadata["error_type"] = e.error_type

        pipeline.gather_metadata()
        pipeline.upload_metadata()

        message.delete()

        logger.info("Processed and deleted msg. Awaiting next one")

    except Exception as e:
        message.delete()
        logger.warning(f"Terminating job due to error {e} with message {message.body}")


def start_pipeline():
    try:
        logger.info(f"Running in {EXECUTION_MODE} mode")
        queue = boto3.resource("sqs").get_queue_by_name(QueueName=os.environ["queue_name"])
        logger.info("Awaiting messages")

        if EXECUTION_MODE == "EC2" or EXECUTION_MODE == "test":
            process_message = process_message_ec2
        else:
            process_message = process_message_hpc

        if PIPELINE_TYPE in ["prefetch", "fasterq-dump"]:
            pipeline_class = Pipeline
        elif PIPELINE_TYPE == "Salmon":
            pipeline_class = SalmonPipeline
        elif PIPELINE_TYPE == "STAR":
            pipeline_class = STARPipeline
        else:
            raise ValueError("Invalid pipeline type")

        if EXECUTION_MODE == "test":
            messages = queue.receive_messages(MaxNumberOfMessages=1, WaitTimeSeconds=5)
            if len(messages) != 0:
                process_message(pipeline_class, messages[0])
        else:
            tries = 0
            while tries < 12:
                messages = queue.receive_messages(MaxNumberOfMessages=1, WaitTimeSeconds=5)
                if len(messages) != 0:
                    process_message(pipeline_class, messages[0])
                    tries = 0
                else:
                    time.sleep(5)
                    tries += 1

            logger.info("No more messages. Terminating.")

            if EXECUTION_MODE == "EC2":
                terminate_itself_in_asg(decrease_capacity=True)

    except Exception as e:
        logger.warning(f"Terminating instance/job due to error {e}")
        if EXECUTION_MODE == "EC2":
            terminate_itself_in_asg(decrease_capacity=False)


if __name__ == "__main__":
    start_pipeline()
