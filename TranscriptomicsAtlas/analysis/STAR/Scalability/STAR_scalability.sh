#!/bin/bash

SRA_IDs=("SRR6192356" "SRR20688788" "SRR11869226")
work_dir="/home/ubuntu/TAtlas"
fastq_dir="$work_dir/fastq"
star_dir="$work_dir/STAR"
csv_file="STAR_exec_times.csv"
threads_array=(16 14 12 10 8 6 4 2 1)

touch $csv_file
echo "n_threads,execution_time_seconds,srr_id,srr_size_MiB,ebs_throughput,ebs_iops,instance_type" >> $csv_file

ebs_throughput=$(aws ec2 describe-volumes --volume-ids vol-0578083bbae20e7b4 --query 'Volumes[*].Throughput' --region us-east-1 | jq -r '.[0]' | awk '{print $1}')
ebs_iops=$(aws ec2 describe-volumes --volume-ids vol-0578083bbae20e7b4 --query 'Volumes[*].Iops' --region us-east-1 | jq -r '.[0]')
instance_id=$(wget -q -O - http://169.254.169.254/latest/meta-data/instance-id)
instance_type=$(aws ec2 describe-instances --instance-ids $instance_id --query 'Reservations[*].Instances[*].[InstanceType]' --output text)

STAR --genomeDir /opt/TAtlas/STAR_data/STAR_index/STAR_index_hg38_gtf_release_111/ --genomeLoad LoadAndExit --outFileNamePrefix $work_dir/STAR_load_index_log/

command_to_run="STAR --genomeDir /opt/TAtlas/STAR_data/STAR_index/STAR_index_hg38_gtf_release_111/ \
	 --genomeLoad LoadAndKeep \
	 --outSAMtype BAM SortedByCoordinate \
	 --outSAMunmapped Within \
	 --quantMode GeneCounts \
	 --limitBAMsortRAM 30064771072 \
	 --outSAMattributes Standard"

for SRA_ID in "${SRA_IDs[@]}"; do
    sra_size=$(ls -l --b=M  /home/ubuntu/TAtlas/sratoolkit/sra/$SRA_ID.sra | cut -d " " -f5 | sed 's/M//')

    for n_threads in "${threads_array[@]}"; do
        echo "Running command with $n_threads threads..."
        start_time=$(date +%s.%N)

        if [[ -e "${fastq_dir}/${SRA_ID}.fastq" ]]; then
            $command_to_run --runThreadN $n_threads --outFileNamePrefix $star_dir/$SRA_ID/ --readFilesIn $fastq_dir/"$SRA_ID".fastq
        else
            $command_to_run --runThreadN $n_threads --outFileNamePrefix $star_dir/$SRA_ID/ --readFilesIn $fastq_dir/"$SRA_ID"_1.fastq $fastq_dir/"$SRA_ID"_2.fastq
        fi

        end_time=$(date +%s.%N)
        execution_time=$(echo "$end_time - $start_time" | bc)

        echo "$n_threads,$execution_time,$SRA_ID,$sra_size,$ebs_throughput,$ebs_iops,$instance_type" >> $csv_file
        echo "Execution time for $SRA_ID with $n_threads threads: $execution_time seconds"
        echo "-----------------------------"
    done
done

echo "Script completed."
