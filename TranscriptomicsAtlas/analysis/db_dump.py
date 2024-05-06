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
    print(df.columns)
    cols_order_star = ["SRR_id",
                       "tissue_name",
                       "STAR_mapping_rate [%]",
                       "SRR_filesize_bytes",
                       "fastq_filesize_bytes",
                       "bam_filesize_bytes",
                       "index_release",
                       "n_spots",
                       "nproc",
                       "instance_type",
                       "library_layout",
                       "instance_id",
                       "execution_mode",
                       "s3_path",
                       "prefetch_start_time",
                       "prefetch_end_time",
                       "fasterq_dump_start_time",
                       "fasterq_dump_end_time",
                       "star_start_time",
                       "star_end_time",
                       "deseq2_star_start_time",
                       "deseq2_star_end_time",
                       "EBS_Iops",
                       "EBS_Size",
                       "EBS_Throughput",
                       "EBS_VolumeType",
                       ]
    cols_order_salmon = ["SRR_id",
                         "tissue_name",
                         "salmon_mapping_rate [%]",
                         "SRR_filesize_bytes",
                         "fastq_filesize_bytes",
                         "index_release",
                         "n_spots",
                         "nproc",
                         "instance_type",
                         "library_layout",
                         "instance_id",
                         "execution_mode",
                         "s3_path",
                         "prefetch_start_time",
                         "prefetch_end_time",
                         "fasterq_dump_start_time",
                         "fasterq_dump_end_time",
                         "salmon_start_time",
                         "salmon_end_time",
                         "deseq2_salmon_start_time",
                         "deseq2_salmon_end_time"]

    cols_order = cols_order_star
    if "error_type" in df.columns:
        cols_order = cols_order[:4] + ["error_type"] + cols_order[4:]

    df = df[cols_order + (list(set(df.columns).difference(cols_order)))]
    df = df.sort_values(["tissue_name", "STAR_mapping_rate [%]"], ascending=[True, False]).reset_index(drop=True)
    df.to_csv(f"data/{table_name}-spot.csv")

    return df


dump_metadata_table("neardata-test-table-7k")
