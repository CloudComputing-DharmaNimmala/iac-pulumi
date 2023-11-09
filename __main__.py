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
identifier = config.require('identifier')
username = config.require('username')
password = config.require('password')
allocated_storage = config.require('allocated_storage')
db_name = config.require('db_name')
engine = config.require('engine')
engine_version = config.require('engine_version')
instance_class = config.require('instance_class')
env_file_path = config.require('env_file_path')

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
    egress=[
        {
            'protocol': "-1",  
            'from_port': 0,
            'to_port': 0, 
            'cidr_blocks': ["0.0.0.0/0"],  
        }
    ],
    tags={
        "Name": "application security group"
    })

#database security group
database_security_group = ec2.SecurityGroup('database-sg',
    description="Database Security Group",
    vpc_id = b_vpc.id,
    ingress=[
        {
            'protocol': 'tcp',
            'from_port': 3306,
            'to_port': 3306,
            'security_groups': [web_app_security_group.id]
        },
    ],
    tags={
        "Name": "database security group"
    })

#create rds parameter group
db_parameter_group = aws.rds.ParameterGroup("mariadb_parameter_group",
    family="mariadb10.6",
    parameters=[
        aws.rds.ParameterGroupParameterArgs(
            name="max_user_connections",
            value=100,
            apply_method="pending-reboot"
        ),
    ],
    name="parametergroup",
    description="parameter_group"
    )

# create a subnet group
rds_subnet_group = aws.rds.SubnetGroup("rds_subnet_group",
    subnet_ids=[subnet.id for subnet in private_subnets],
    tags={
        "Name": "My RDS subnet group",
    })



# create rds instance
rds_instance = aws.rds.Instance("rds_instance",
    identifier=identifier,
    multi_az=False,
    username=username,
    password=password,
    allocated_storage=allocated_storage,
    db_name=db_name,
    engine=engine,
    engine_version=engine_version,
    instance_class=instance_class,
    parameter_group_name=db_parameter_group.name,
    skip_final_snapshot=True,
    db_subnet_group_name=rds_subnet_group.name,
    publicly_accessible=False,
    vpc_security_group_ids=[database_security_group.id]
    )

# Create an IAM role
cloudwatch_agent_server_role = aws.iam.Role(
    "cloudwatch-agent-server-role",
    assume_role_policy="""{
      "Version": "2012-10-17",
      "Statement": [
        {
          "Effect": "Allow",
          "Principal": {
            "Service": "ec2.amazonaws.com"
          },
          "Action": "sts:AssumeRole"
        }
      ]
    }""",
)

# Attach the CloudWatchAgentServerPolicy
cloudwatch_agent_server_policy_attachment = aws.iam.PolicyAttachment(
    "cloudwatch-agent-server-policy-attachment",
    policy_arn="arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy",
    roles=[cloudwatch_agent_server_role.name],
)

test_profile = aws.iam.InstanceProfile("testProfile", role=cloudwatch_agent_server_role.name)
# Create an EC2 instance
ec2_instance = ec2.Instance(
    "My-Ami-Instance",
    ami=my_ami_id,
    instance_type=my_instance_type,  # Choose the appropriate instance type
    subnet_id=public_subnets[0].id,  # Replace with the desired subnet ID
    security_groups=[web_app_security_group.id],  # Attach the security group
    associate_public_ip_address=True,
    key_name=key_name,
    iam_instance_profile = test_profile.name,
    root_block_device={
        "volume_size": 25,
        "volume_type": "gp2",  
        "delete_on_termination": True,
    },
    tags={
        "Name": "my-ami-instance",  # Provide a name for your instance
    },
    user_data=pulumi.Output.all(endpoint=rds_instance.endpoint
    ).apply(
        lambda args: f"""#!/bin/bash
NEW_DB_USER={username}
NEW_DB_PASSWORD={password}
NEW_DB_HOST={args["endpoint"].split(":")[0]}
NEW_DB_NAME={db_name}
ENV_FILE_PATH={env_file_path}

if [ -e "$ENV_FILE_PATH" ]; then
sed -i -e "s/DB_HOST=.*/DB_HOST=$NEW_DB_HOST/" \
-e "s/DB_USER=.*/DB_USER=$NEW_DB_USER/" \
-e "s/DB_PASSWORD=.*/DB_PASSWORD=$NEW_DB_PASSWORD/" \
-e "s/DB_NAME=.*/DB_NAME=$NEW_DB_NAME/" \
"$ENV_FILE_PATH"
else
echo "$ENV_FILE_PATH not found."
fi

sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
-a fetch-config \
-m ec2 \
-c file:/opt/csye6225/webapp/cloudwatch-config.json \
-s
sudo systemctl restart amazon-cloudwatch-agent"""),
)

www = aws.route53.Record("www",
    zone_id="Z10302201POPYII3KMF2G",
    name="demo.mynscc.me",
    type="A",
    ttl=60,
    records=[ec2_instance.public_ip])

