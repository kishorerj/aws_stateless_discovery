

import argparse
from concurrent.futures import ThreadPoolExecutor, wait
import csv, traceback
import datetime
import logging
import os
import sys
import time
import zipfile

import boto3
from pkg_resources import parse_version as version




as_list= []
as_vm_list = []
as_tg_list=[]

start = time.time()
region_counter = 0

austoscaling_info = {
    'AutoScalingGroupName':'',
    'LaunchTemplateName':'',
    'Region':'',
    'LaunchConfigurationName':'',
    'MinSize':'',
    'MaxSize':'',
    'DesiredSize':'',
    'LoadBalancerTargetGroup':0,
    'AvailabilityZone':0,
    'VPC':'',
    'Tags':0,
    'LoadBalancerName':0,
    'CreatedDate':'', 
}

austoscaling_vm_instances = {
    'ASGroupName':'',
    'LaunchTemplateName':'',
    'LaunchConfigurationeName':'',
    'InstanceType':'',
    'LifecycleState':'',
    'HealthStatus':'',    
}

austoscaling_target_groups = {
    'AutoScalingGroupName':'',
    'TargetGroupName':'',
    'TargetGroupArn':'',
    'LoadbalancerName':'',
    'LoadbalancerArn':'',
    'DomainName':'',    
}

as_field_names = ['AutoScalingGroupName', 'LaunchTemplateName', 'Region', 'LaunchConfigurationName','MinSize',
    'MaxSize', 'DesiredSize','LoadBalancerTargetGroup', 'AvailabilityZone', 'VPC', 'Tags', 'LoadBalancerName', 'CreatedDate']
as_vms_field_names = [
        'AutoScalingGroupName',
        'LaunchTemplateName',
        'LaunchConfigurationeName',
        'InstanceType',
        'LifecycleState',
        'HealthStatus'   
    ]
as_tg_field_names = [
    'AutoScalingGroupName',
    'TargetGroupName',
    'TargetGroupArn',
    'LoadBalancerName',
    'LoadBalancerArn',
    'DNSName',    
    ]



def create_directory(dir_name):
  """Create output directory.
  Args:
    dir_name: Destination directory
  """
  try:
    if not os.path.exists(dir_name):
      os.makedirs(dir_name)
  except Exception as e:
    logging.error('error in create_directory')
    logging.error(e)



def write_to_csv(dictionary_data, field_name_list, file_name):
  
  try:
    logging.info('Writing %s to the disk', file_name)
    with open('./out/'+file_name, 'w', newline='') as csvfile:
      writer = csv.DictWriter(csvfile, fieldnames=field_name_list,
                              extrasaction='ignore')
      writer.writeheader()
      for dictionary_value in dictionary_data:
        writer.writerow(dictionary_value)
  except Exception as e:
    logging.error('error in report_writer')
    logging.error(e)





def display_script_progress():
  try:
    sys.stdout.write('\r')
    sys.stdout.write('%s[%s%s] %i/%i\r' % ('Regions: ', '#'*region_counter,
                                           '.'*(total_regions-region_counter),
                                           region_counter, total_regions))
    sys.stdout.flush()
  except Exception as e:
    logging.error('error in method display script')
    logging.error(e)





def zip_files(dir_name, zip_file_name):
  """Compress generated files into zip file for import into stratozone.
  Args:
    dir_name: source directory
    zip_file_name: name of the file to be created
  """
  csv_filter = lambda name: 'csv' in name

  if os.path.exists(zip_file_name):
    os.remove(zip_file_name)

  with zipfile.ZipFile(zip_file_name, 'w') as zip_obj:
    # Iterate over all the files in directory
    for folder_name, subfolders, file_names in os.walk(dir_name):
      for file_name in file_names:
        if csv_filter(file_name):
          file_path = os.path.join(folder_name, file_name)
          zip_obj.write(file_path, os.path.basename(file_path))




def set_instances(as_instance,launch_template, region_name):
    vm_instances= as_instance.get('Instances')
    for vm_instance in vm_instances:
        as_vms = austoscaling_vm_instances.copy()

        as_vms['AutoScalingGroupName']= as_instance.get('AutoScalingGroupName'),
        as_vms['LaunchTemplateName'] = launch_template
        as_vms['LaunchConfigurationName'] = as_instance.get('LaunchConfigurationName')
        as_vms['InstanceType'] = vm_instance.get('InstanceType')
        as_vms['LifecycleState'] = vm_instance.get('LifecycleState')
        as_vms['HealthStatus'] = vm_instance.get('HealthStatus')

        as_vm_list.append(as_vms)


def set_target_groups(as_instance, region_name):
    client = boto3.client('elbv2', region_name)
    as_name=as_instance.get('AutoScalingGroupName')
    print(as_name , as_instance.get('TargetGroupARNs'))
    
    if(as_instance.get('TargetGroupARNs')):
    
      target_groups=client.describe_target_groups(
          TargetGroupArns=as_instance.get('TargetGroupARNs')
          
      )
      print(target_groups)
      for tg in target_groups.get('TargetGroups'):
          if(tg.get('LoadBalancerArns')):
            loadbalancers = client.describe_load_balancers(
            LoadBalancerArns=
                tg.get('LoadBalancerArns') )
            print(loadbalancers)
            for lb in loadbalancers.get('LoadBalancers'):
                tg_info=austoscaling_target_groups.copy()
                tg_info['AutoScalingGroupName']=as_name
                tg_info['TargetGroupName']=tg.get('TargetGroupName')
                tg_info['TargetGroupArn']=tg.get('TargetGroupArn')
                tg_info['LoadBalancerArn']= tg.get('LoadBalancerArn')
                tg_info['LoadBalancerName']= lb.get('LoadBalancerName')
                tg_info['DNSName']= lb.get('DNSName')

                as_tg_list.append(tg_info)



if version(boto3.__version__) < version('1.20.30'):
  print("Please use a version of boto3 > 1.20.30")
  exit()


# create output and log directory
create_directory('./out')

log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(filename='./out/aws-as-info.log',
                    format=log_format,
                    level=logging.ERROR)


ec2_client = boto3.client('ec2')
as_client = boto3.client('autoscaling')


logging.info('Get all regions')
regions = ec2_client.describe_regions(AllRegions=True)

logging.info('Get Organization ID')



for region in regions['Regions']:
    total_regions = len(regions['Regions'])
    region_counter += 1
    print(region['RegionName'])
    try: 
      client = boto3.client('autoscaling',  region['RegionName'])
   

      display_script_progress()

      autoscaling_groups= client.describe_auto_scaling_groups()
    except:
      print("Exception occured")
      continue    

    for as_instance in autoscaling_groups.get('AutoScalingGroups'): 
        as_info = austoscaling_info.copy()
        as_info['AutoScalingGroupName']= as_instance.get('AutoScalingGroupName')
        launch_template=''
        if(as_instance.get('MixedInstancesPolicy') is not None):
         launch_template=  as_instance.get('MixedInstancesPolicy').get('LaunchTemplate').get('LaunchTemplateSpecification').get('LaunchTemplateName')
        
        as_info['LaunchTemplateName']= launch_template
        as_info['Region']= region['RegionName']
        as_info['LaunchConfigurationName'] = as_instance.get('LaunchConfigurationName')
        as_info['MinSize'] = as_instance.get('MinSize')
        as_info['MaxSize'] = as_instance.get('MaxSize')
        as_info['DesiredCapacity'] = as_instance.get('DesiredCapacity')
        as_info['AvailabilityZone'] = as_instance.get('AvailabilityZones')
        as_info['VPC'] = as_instance.get('VPCZoneIdentifier')
        as_info['Tags'] = as_instance.get('Tags')
        as_info['LoadBalancerName'] = as_instance.get('LoadBalancerNames')
        as_info['CreatedDate'] = as_instance.get('CreatedTime')
        as_list.append(as_info)
        try:
            set_target_groups(as_instance,  region['RegionName'])        
            set_instances(as_instance,launch_template,  region['RegionName'])
        except:
            print("Exception while setting target groups")
            # printing stack trace
            traceback.print_exc()
            continue

        

write_to_csv(as_list, as_field_names, 'as_info.csv')
write_to_csv(as_vm_list, as_vms_field_names, 'as_vms.csv')
write_to_csv(as_tg_list, as_tg_field_names, 'as_targetgroups.csv')






