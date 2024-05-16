#!/usr/bin/env bash
/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -c ssm:ec2_cwagent_config -s
# rm -rf because sync below is unreliable
rm -rf /opt/TAtlas/Consumer /opt/TAtlas/DESeq2
aws s3 sync s3://neardata-src/source/Salmon /opt/TAtlas

{
echo export queue_name="Salmon_queue"
echo export s3_bucket_name="neardata-salmon-test-7k"
echo export dynamodb_metadata_table="neardata-test-salmon-ec2-7k"
echo export execution_mode="EC2"
echo export pipeline_type="Salmon"
echo export index_release="111"
echo export INTERRUPTION_MONITORING="True"
} >> /etc/environment

# temp fix to save instance id for future use during metric collection
INSTANCE_ID=$(curl -s http://169.254.169.254/latest/meta-data/instance-id)
aws dynamodb put-item --table-name neardata-instance-ids --item "{\"instance_id\": {\"S\": \"$INSTANCE_ID\"}}" --region=us-east-1

su ubuntu -c "python3 /opt/TAtlas/Consumer/consumer.py"