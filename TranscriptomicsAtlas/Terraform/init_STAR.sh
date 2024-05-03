#!/usr/bin/env bash
/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -c ssm:ec2_cwagent_config -s
#/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -m ec2 -a stop
# rm -rf because sync below is unreliable
rm -rf /opt/TAtlas/Consumer /opt/TAtlas/DESeq2
aws s3 sync s3://neardata-src/source/STAR/ /opt/TAtlas

{
echo export queue_name="STAR_queue"
echo export s3_bucket_name="neardata-star-test-7k"
echo export dynamodb_metadata_table="neardata-test-table-7k"
echo export execution_mode="EC2"
echo export pipeline_type="STAR"
echo export index_release="111"
echo export INTERRUPTION_MONITORING="True"
} >> /etc/environment

# temp fix to save instance id for future use during metric collection
INSTANCE_ID=$(curl -s http://169.254.169.254/latest/meta-data/instance-id)
aws dynamodb put-item --table-name neardata-instance-ids --item "{\"instance_id\": {\"S\": \"$INSTANCE_ID\"}}" --region=us-east-1

aws s3 cp s3://neardata-src/STAR_data/STAR_ref/SRR11982817-ref/ReadsPerGene.out.tab /opt/TAtlas/STAR_data/STAR_ref/SRR11982817-ref/ReadsPerGene.out.tab

## NFS mount
mkdir /opt/TAtlas/STAR_data/STAR_index/ -p
mount.nfs4 10.0.1.100:/ /opt/TAtlas/STAR_data/STAR_index/

su ubuntu -c "python3 /opt/TAtlas/Consumer/consumer.py"