# Discover Stateless AWS Autoscaling ghroups

## Overview
This script invokes the necessary APIs in AWS to obtain the details of Autoscaling groups, along with details of the load balancers front ending these and the 
VM instances created during scaling of the Autoscaling groups. In particular it collects information on
* Details of autoscaling groups and their configuration
* The Launch templates or Lauunch configuration associated with these AS groups.
* The Target groups and Load balancers front ending these Autoscaling groups.
* The Virtual machines aloing with machine family details that running as a result of scaling.

By running this script in AWS it is possible to estimate the AWS workloads created because of Autoscaling groups and plan the GCP workloads based on this .
It is highly recommended to validate the number of autoscaling groups listed in this script with the one in console to ensure correctness.


## Script execution 

Step 1: Login to AWS Console

Step 2: Launch Cloud Shell
"Image of Cloud Shell Console highlighting an icon with a greater-than and underscore"

Step 3: Clone project to local shell

git clone https://github.com/kishorerj/aws_stateless_discovery.git

Step 4: Run script to start collection
python3 aws-instancegroup-export.py



## Output files

* as-info.csv : Contains details of autoscaling groups along with the Launch template details
* as_targetgroups.csv : Contains details of the target groups and load balancers in AWS front ending each Autoscaling groups
* as_vms.csv: Contains details of the VMs along with their machine family types created during scaling of Autoscaling groups.

