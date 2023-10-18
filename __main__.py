import pulumi
from pulumi_aws import ec2
import pulumi_aws as aws
 
config = pulumi.Config()
public_subnet_config =config.require_object('public_subnet_configs')
private_subnet_config =config.require_object('private_subnet_configs')
dest_cidr = config.require('destination_cidr')
main_vpc_cider_block = config.require('main_vpc_cider_block')
main_vpc = config.require('main_vpc_name')
main_igw = config.require('main_igw_name')
public_route_table = config.require('public_route_table_name')
private_route_table = config.require('private_route_table_name')
ssh_cidr_block = config.require_object('ssh_cidr_block')
http_cidr_block = config.require_object('http_cidr_block')
https_cidr_block = config.require_object('https_cidr_block')
app_port_cidr_block = config.require_object('app_port_cidr_block')
app_port = config.require_object('app_port')
key_name = config.require('key_name')
my_ami_id = config.require('my_ami_id')
my_instance_type = config.require('instance_type')

#creating VPC
b_vpc = ec2.Vpc('main_vpc', 
                cidr_block = main_vpc_cider_block, 
                enable_dns_hostnames=True, 
                enable_dns_support=True, 
                tags={
                    "Name": main_vpc
                    })

# Create an Internet Gateway (IGW)
igw = ec2.InternetGateway('main_igw',
                         vpc_id=b_vpc.id,
                         tags={
                             "Name": main_igw
                         })

# Fetch availability zones for the current region
availability_zones = aws.get_availability_zones(
    state= "available"
)

# Determine how many availability zones to use (min of 3, max of available zones)
num_of_azs = min(3, len(availability_zones.names))

# Create public subnets in selected availability zones
public_subnets = []
for i in range(num_of_azs):
    az = availability_zones.names[i]
    config = public_subnet_config[i]  # Use the corresponding config for the zone
    subnet = ec2.Subnet(config["name"],
                       vpc_id=b_vpc.id,
                       cidr_block=config["cidr_block"],
                       availability_zone=az,
                       tags={
                           "Name": config["name"],
                       })
    public_subnets.append(subnet)

# Create private subnets in selected availability zones
private_subnets = []
for i in range(num_of_azs):
    az = availability_zones.names[i]
    config = private_subnet_config[i]  # Use the corresponding config for the zone
    subnet = ec2.Subnet(config["name"],
                       vpc_id=b_vpc.id,
                       cidr_block=config["cidr_block"],
                       availability_zone=az,
                       tags={
                           "Name": config["name"],
                       })
    private_subnets.append(subnet)



# Create a public route table and associate it with public subnets
public_route_table = ec2.RouteTable('public_route_table',
                                    vpc_id=b_vpc.id,
                                    routes = [
                                        {
                                            'cidr_block': dest_cidr,  
                                            'gateway_id': igw.id,  
                                        },
                                     ],
                                    tags={"Name": public_route_table})

# Create a private route table and associate it with private subnets
private_route_table = ec2.RouteTable('private_route_table',
                                      vpc_id=b_vpc.id,
                                      tags={"Name": private_route_table})

# Iterate through public subnets and associate them with the public route table
for n,subnet in enumerate(public_subnets):
    ec2.RouteTableAssociation(f"public_route_table_association{n}",
                             route_table_id=public_route_table.id,
                             subnet_id=subnet.id)
    
# Iterate through public subnets and associate them with the public route table
for n,subnet in enumerate(private_subnets):
    ec2.RouteTableAssociation(f"private_route_table_association{n}",
                             route_table_id=private_route_table.id,
                             subnet_id=subnet.id)
    
#security group
web_app_security_group = ec2.SecurityGroup('web-app-sg',
    description="Application Security Group",
    vpc_id = b_vpc.id,
    ingress=[
        {
            'protocol': 'tcp',
            'from_port': 22,
            'to_port': 22,
            'cidr_blocks': ssh_cidr_block,  # SSH from my system
        },
        {
            'protocol': 'tcp',
            'from_port': 80,
            'to_port': 80,
            'cidr_blocks': http_cidr_block,  # HTTP from anywhere
        },
        {
            'protocol': 'tcp',
            'from_port': 443,
            'to_port': 443,
            'cidr_blocks': https_cidr_block,  # HTTPS from anywhere
        },
        {
            'protocol': 'tcp',
            'from_port': app_port,  # Replace with your application's port
            'to_port': app_port,    # Replace with your application's port
            'cidr_blocks': app_port_cidr_block,  # Your application's port from anywhere
        },
    ],
    tags={
        "Name": "application security group"
    })


# Create EC2
# Define your custom AMI (replace with your actual AMI ID)
custom_ami = my_ami_id


# Create an EC2 instance
ec2_instance = ec2.Instance(
    "My-Ami-Instance",
    ami=custom_ami,
    instance_type=my_instance_type,  # Choose the appropriate instance type
    subnet_id=public_subnets[0].id,  # Replace with the desired subnet ID
    security_groups=[web_app_security_group.id],  # Attach the security group
    associate_public_ip_address=True,
    key_name=key_name,
    root_block_device={
        "volume_size": 25,
        "volume_type": "gp2",  # General Purpose SSD (GP2)
        "delete_on_termination": True,
    },
    tags={
        "Name": "my-ami-instance",  # Provide a name for your instance
    },
)
