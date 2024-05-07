import os
import boto3
import requests

aws_metadata_url = 'http://169.254.169.254/latest/meta-data/'


def srr_id_in_metadata_table(table, SRR_id):
    if "Item" in table.get_item(Key={"SRR_id": SRR_id}):
        return True
    return False


def get_instance_id():
    execution_mode = os.environ.get("execution_mode", None)
    if execution_mode == "EC2":
        instance_id = requests.get(aws_metadata_url + 'instance-id').text
    elif execution_mode == "Fargate":
        instance_id = os.environ["ECS_CONTAINER_METADATA_URI_V4"].split("http://169.254.170.2/v4/")[1]
    elif execution_mode == "HPC_container":
        instance_id = os.environ["HOSTNAME"] + "/" + os.environ.get("SLURM_JOB_ID", "") + "/" + os.environ.get("SLURM_ARRAY_TASK_ID", "")
    else:
        instance_id = "N/A"

    return instance_id


def get_ssm_parameter(param_name):
    ssm = boto3.client("ssm")
    ssm_param = ssm.get_parameter(Name=param_name, WithDecryption=True)
    param_value = ssm_param['Parameter']['Value']
    return param_value


def get_aws_instance_metadata(metadata):
    instance_id = requests.get(aws_metadata_url + 'instance-id').text

    ec2 = boto3.client('ec2')
    response = ec2.describe_instances(InstanceIds=[instance_id])
    ec2_metadata = response["Reservations"][0]["Instances"][0]
    volume_id = ec2_metadata['BlockDeviceMappings'][0]['Ebs']['VolumeId']
    volume_metadata = ec2.describe_volumes(VolumeIds=[volume_id])
    instance_type = requests.get(aws_metadata_url + 'instance-type').text

    metadata["instance_type"] = instance_type
    metadata["EBS_Size"] = volume_metadata["Volumes"][0]["Size"]
    metadata["EBS_Iops"] = volume_metadata["Volumes"][0]["Iops"]
    metadata["EBS_VolumeType"] = volume_metadata["Volumes"][0]["VolumeType"]
    metadata["EBS_Throughput"] = volume_metadata["Volumes"][0]["Throughput"]
