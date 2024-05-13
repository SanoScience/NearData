#!/bin/env bash
#SBATCH -J salmon_container
#SBATCH -N 1
#SBATCH --ntasks-per-node=4
#SBATCH --mem-per-cpu=8GB
#SBATCH --time=03:00:00
#SBATCH -A plgsano5-cpu
#SBATCH -p plgrid
#SBATCH --output="output/output-%A_%a.out"
#SBATCH --error="error/error-%A_%a.err"

apptainer run --home /home/ubuntu --compat \
              --mount type=bind,source=/net/people/plgrid/plgpkica/.aws/,destination=/home/ubuntu/.aws/ \
              --mount type=bind,source=/net/people/plgrid/plgpkica/.ncbi/,destination=/home/ubuntu/.ncbi/ \
              --mount type=bind,source=$TMPDIR,destination=/home/ubuntu/TAtlas \
              --env AWS_SHARED_CREDENTIALS_FILE=/home/ubuntu/.aws/credentials \
              --env SLURM_JOB_ID=$SLURM_JOB_ID \
              /net/ascratch/people/plgpkica/neardata/salmonpipeline.sif
