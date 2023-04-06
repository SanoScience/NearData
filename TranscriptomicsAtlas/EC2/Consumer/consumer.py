import os
import subprocess
from time import sleep
from pathlib import Path

import requests

import boto3
import botocore
import watchtower, logging

metadata_url = 'http://169.254.169.254/latest/meta-data/'
os.environ['AWS_DEFAULT_REGION'] = requests.get(metadata_url + 'placement/region').text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.addHandler(watchtower.CloudWatchLogHandler(send_interval=1))

#  Retrieve queue_name from Parameter Store
ssm = boto3.client("ssm")
queue_name_paramter = ssm.get_parameter(Name="/neardata/queue_name", WithDecryption=True)
queue_name = queue_name_paramter['Parameter']['Value']

s3_bucket_paramter = ssm.get_parameter(Name="/neardata/s3_bucket_name", WithDecryption=True)
s3_bucket_name = s3_bucket_paramter['Parameter']['Value']

sqs = boto3.resource("sqs")
queue = sqs.get_queue_by_name(QueueName=queue_name)

s3 = boto3.resource('s3')


def consume_message(msg_body):
    srr_id = msg_body

    ### Check if file exists in S3, if yes then skip ###
    try:  # TODO replace try-except with listing files?  https://stackoverflow.com/questions/33842944/check-if-a-key-exists-in-a-bucket-in-s3-using-boto3
        logger.info("Checking if the pipeline has already been run")
        s3.Object("neardata-bucket-123", f'normalized_counts/{srr_id}/{srr_id}_normalized_counts.txt').load()
        logger.debug("File exisits, exiting")
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] != "404":
            logger.debug(e)
            return
        logger.info("File not found, starting the pipeline")

    ###  Downloading SRR file ###            # TODO extract each step to separate function?
    logger.info(f"Starting prefetch of {srr_id}")
    # subprocess.run(
    #     [f"prefetch", msg_body]  #  TODO replace with S3 cpy if file available in bucket
    # )
    logger.info(f"Prefetched {srr_id}")

    ###  Unpacking SRR to .fastq using fasterq-dump ###
    fastq_dir = f"/home/ubuntu/fastq/{srr_id}"
    os.makedirs(fastq_dir, exist_ok=True)  # TODO exist_ok=True? for now
    logger.info("Starting unpacking the SRR file using fasterq-dump")
    # subprocess.run(
    #     ["fasterq-dump", srr_id, "--outdir", fastq_dir]
    # )
    logger.info("Unpacking finished")

    ###  Quantification using Salmon ###
    index_path = "/home/ubuntu/index/human_transcriptome_index"
    quant_dir = f"/home/ubuntu/salmon/{srr_id}"
    os.makedirs(quant_dir, exist_ok=True)
    logger.info("Quantification starting")
    # subprocess.run(
    #     ["salmon", "quant", "-p", "2", "--useVBOpt", "-i", index_path, "-l", "A", "-1", f"{fastq_dir}_1.fastq", "-2",
    #      f"{fastq_dir}_2.fastq", "-o", quant_dir]  # TODO check args
    # )
    # sleep(30)
    logger.info("Quantification finished")

    ### Run R script on quant.sf

    # Update samples.txt script with correct SRR_ID
    with open("/home/ubuntu/DESeq2/samples.txt", "w") as f:
        f.write(f"""samples	pop	center	run	condition\n{srr_id}	1.1	HPC	{srr_id}	stimulus""")

    logger.info("DESeq2 starting")
    subprocess.run(  # TODO consider capturing some logs from subprocess steps
        ["Rscript", "DESeq2/salmon_to_deseq.R", srr_id], stderr=subprocess.DEVNULL  # TODO modify Rscript import so it doesn't print unnecessary output to stderr
    )
    logger.info("DESeq2 finished")

    ### Upload normalized counts to S3 ###
    logger.info("S3 upload starting")
    # s3.meta.client.upload_file(f'/home/ubuntu/R_output/{srr_id}_normalized_counts.txt', s3_bucket_name,
    #                            f"normalized_counts/{srr_id}/{srr_id}_normalized_counts.txt")
    logger.info("S3 upload finished")

    ### Clean all input and output files ###
    def clean_dir(path):
        for f in Path(path).glob("*"):
            if f.is_file():
                f.unlink()

    logger.info("Starting removing generated files")
    # clean_dir("/home/ubuntu/sratoolkit/sra")
    # clean_dir("/home/ubuntu/fastq")
    # clean_dir("/home/ubuntu/salmon")
    clean_dir("/home/ubuntu/R_output")
    logger.info("Finished removing generated files")


if __name__ == "__main__":
    logger.info("Awaiting messages")
    while True:
        messages = queue.receive_messages(MaxNumberOfMessages=1)  # TODO check args
        for message in messages:
            logger.info(f"Received msg={message.body}")
            consume_message(message.body)
            message.delete()