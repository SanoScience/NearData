#!/usr/bin/env bash

# https://askubuntu.com/questions/1367139/apt-get-upgrade-auto-restart-services
sudo apt-get remove needrestart -y

sudo apt-get update
sudo apt-get install awscli wget ca-certificates -y  --no-install-recommends

sudo chown -R ubuntu /opt
### SRA-TOOLKIT
mkdir -p /home/ubuntu/TAtlas/sratoolkit
wget https://ftp-trace.ncbi.nlm.nih.gov/sra/sdk/3.0.1/sratoolkit.3.0.1-ubuntu64.tar.gz -O - | tar -zx -C /opt/TAtlas
echo 'export PATH="$PATH":/opt/TAtlas/sratoolkit.3.0.1-ubuntu64/bin' >> ~/.bashrc

#### STAR
wget https://github.com/alexdobin/STAR/archive/2.7.10b.tar.gz -O - | tar -zx -C /opt/TAtlas
echo 'export PATH="$PATH":/opt/TAtlas/STAR-2.7.10b/bin/Linux_x86_64' >> ~/.bashrc

### PYTHON MODULES
sudo apt-get install python3-pip -y --no-install-recommends
pip3 install boto3 watchtower requests backoff --no-cache-dir

### R
wget -qO- https://cloud.r-project.org/bin/linux/ubuntu/marutter_pubkey.asc | sudo tee -a /etc/apt/trusted.gpg.d/cran_ubuntu_key.asc
sudo add-apt-repository "deb https://cloud.r-project.org/bin/linux/ubuntu $(lsb_release -cs)-cran40/" -y
sudo apt-get install --no-install-recommends r-base-dev -y

### R packages
# 'DESeq2', 'RCurl', 'RcppArmadillo' (libraries required by DESeq2) require
sudo apt-get install libxml2-dev libssl-dev libcurl4-openssl-dev libopenblas-dev  -y

sudo chmod o+w /usr/local/lib/R/site-library/
Rscript -e 'install.packages(c("readr", "dplyr", "BiocManager", "jsonlite", "data.table"))'
Rscript -e 'BiocManager::install(c("DESeq2", "tximport"))'

### CWAGENT
sudo wget https://s3.amazonaws.com/amazoncloudwatch-agent/debian/amd64/latest/amazon-cloudwatch-agent.deb
sudo dpkg -i -E ./amazon-cloudwatch-agent.deb
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -c ssm:ec2_cwagent_config -s
sudo rm amazon-cloudwatch-agent.deb

### Source Codes
mkdir /opt/TAtlas/STAR_data/STAR_index_mount -p
aws s3 sync s3://neardata-src/source/STAR/ /opt/TAtlas/
aws s3 sync s3://neardata-src/STAR_data/STAR_ref/ /opt/TAtlas/STAR_data/STAR_ref/