import boto3
import pandas as pd


def dump_metadata_table(table_name):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)

    db = []
    start_key = None
    while True:
        if not start_key:
            response = table.scan()
        else:
            response = table.scan(ExclusiveStartKey=start_key)
        db.extend(response.get('Items', []))
        start_key = response.get('LastEvaluatedKey', None)
        if start_key is None:
            break

    df = pd.DataFrame(db)
    df = df[["SRR_id",
             "bucket",
             "tissue_name",
             "error_type",
             "salmon_mapping_rate [%]",
             "SRR_filesize_bytes",
             "fastq_filesize_bytes",
             "execution_mode",
             "instance_id",
             "prefetch_start_time",
             "prefetch_end_time",
             "fasterq_dump_start_time",
             "fasterq_dump_end_time",
             "salmon_start_time",
             "salmon_end_time",
             "deseq2_start_time",
             "deseq2_end_time"]]
    df = df.sort_values(["tissue_name", "salmon_mapping_rate [%]"], ascending=[True, False]).reset_index(drop=True)
    df.to_csv("data/metadata_db_dump_HPC.csv")

    return df


dump_metadata_table("neardata-tissues-salmon-metadata")