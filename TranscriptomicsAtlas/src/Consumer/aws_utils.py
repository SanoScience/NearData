import os
import boto3
import requests
import subprocess

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


def terminate_itself_in_asg(decrease_capacity):
    asg = boto3.client("autoscaling")
    instance_id = requests.get('http://169.254.169.254/latest/meta-data/instance-id').text
    asg.terminate_instance_in_auto_scaling_group(InstanceId=instance_id, ShouldDecrementDesiredCapacity=decrease_capacity)


def get_ec2_instance_metadata(metadata):
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


def get_fargate_instance_metadata(metadata):
    ecs_metadata_url = os.environ["ECS_CONTAINER_METADATA_URI_V4"]
    ecs_metadata_response = requests.get(ecs_metadata_url).json()
    cluster_id, task_id = ecs_metadata_response["Labels"]['com.amazonaws.ecs.task-arn'].split("/")[1:3]
    task_metadata_response = boto3.client("ecs").describe_tasks(cluster=cluster_id, tasks=[task_id])

    volumes = task_metadata_response["tasks"][0]["attachments"]
    for volume in volumes:
        if volume["type"] == "AmazonElasticBlockStorage":  # assuming only one attachment of EBS
            for vol_detail in volume["details"]:
                if vol_detail["name"] == "volumeId":
                    volume_id = vol_detail["value"]
                    break

    volume_metadata = boto3.client("ec2").describe_volumes(VolumeIds=[volume_id])
    metadata["EBS_Size"] = volume_metadata["Volumes"][0]["Size"]
    metadata["EBS_Iops"] = volume_metadata["Volumes"][0]["Iops"]
    metadata["EBS_VolumeType"] = volume_metadata["Volumes"][0]["VolumeType"]
    metadata["EBS_Throughput"] = volume_metadata["Volumes"][0]["Throughput"]
    metadata["cpu_model"] = subprocess.check_output("lscpu | grep 'Model name'", shell=True, text=True).split(":")[1].strip()