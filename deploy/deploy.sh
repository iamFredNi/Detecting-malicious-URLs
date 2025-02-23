#!/bin/sh

set -e

# Save PWD
tmp=$(echo $PWD)
cd $( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

source ../.venv/bin/activate

# Setup lambda files and layer
echo Zipping function code...
cd ../src/social_network_crawler
zip -q ../../deploy/lambda_function.zip ./lambda_function.py
cd ../../deploy

echo Creating lambda layer directory and installing dependencies...
mkdir -p ./layer/python/src
pip install -q -q -q -r ../REQUIREMENTS.txt -t ./layer/python
cp -r ../src  ./layer/python


echo Zipping lambda layer...
cd ../deploy/layer
zip -q -r ../layer.zip .
cd ..

# deploy with Terraform
cd terraform
terraform init && terraform apply --auto-approve
cd ..

# clean lambda deployment files
rm -rf ./layer
rm ./lambda_function.zip
rm ./layer.zip

# wait for servers to boot...
sleep 30

# run ansible
cd ./ansible
ansible-playbook -i hosts.ini playbook.yml

# Restore PWD
cd $tmp