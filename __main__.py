import pulumi
from pulumi_aws import ec2 
 
config = pulumi.Config()
public_subnet_config =config.require_object('public_subnet_configs')
private_subnet_config =config.require_object('private_subnet_configs')
dest_cidr = config.require('destination_cidr')
main_vpc_cider_block = config.require('main_vpc_cider_block')
main_vpc = config.require('main_vpc_name')
main_igw = config.require('main_igw_name')
public_route_table = config.require('public_route_table_name')
private_route_table = config.require('private_route_table_name')


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

#creating public subnets
public_subnets = []
for config in public_subnet_config:
    subnet = ec2.Subnet(config["name"],
        vpc_id=b_vpc.id,
        cidr_block=config["cidr_block"],

        availability_zone=config["availability_zone"],
        tags={
            "Name": config["name"],
        })
    public_subnets.append(subnet)

# creating private subnets
private_subnets = []
for config in private_subnet_config:
    subnet = ec2.Subnet(config["name"],
        vpc_id=b_vpc.id,
        cidr_block=config["cidr_block"],
        availability_zone=config["availability_zone"],
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
    
