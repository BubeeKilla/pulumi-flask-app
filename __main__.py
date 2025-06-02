import pulumi
import pulumi_aws as aws
from pulumi_aws import ecs, ec2, iam, lb, ecr
from pulumi_docker import Image
import base64
import time
import random
import json


def get_container_def(name: str):
    return json.dumps([
        {
            "name": "flask-app",
            "image": f"{name}:latest",
            "portMappings": [
                {"containerPort": 5000, "protocol": "tcp"}
            ],
            "environment": [
                {
                    "name": "TASK_AZ",
                    "value": azs[0]
                }
            ],
            "logConfiguration": {
                "logDriver": "awslogs",
                "options": {
                    "awslogs-group": "/ecs/flask-task",
                    "awslogs-region": "eu-central-1",
                    "awslogs-stream-prefix": "flask"
                }
            }
        }
    ])

# 1. Get 2 Availability Zones
azs = aws.get_availability_zones(state="available").names[:2]

# 2. Create a new VPC
vpc = ec2.Vpc("flask-vpc", cidr_block="10.0.0.0/16")

# 3. Create subnets in 2 AZs
subnets = []
for i, az in enumerate(azs):
    subnet = ec2.Subnet(f"flask-subnet-{i}",
        vpc_id=vpc.id,
        cidr_block=f"10.0.{i}.0/24",
        availability_zone=az,
        map_public_ip_on_launch=True
    )
    subnets.append(subnet)

# 4. Internet Gateway
igw = ec2.InternetGateway("flask-igw", vpc_id=vpc.id)

# 5. Route Table
route_table = ec2.RouteTable("flask-route-table",
    vpc_id=vpc.id,
    routes=[{
        "cidr_block": "0.0.0.0/0",
        "gateway_id": igw.id,
    }]
)

# 6. Associate Route Table to Subnets
for i, subnet in enumerate(subnets):
    ec2.RouteTableAssociation(f"flask-rta-{i}",
        subnet_id=subnet.id,
        route_table_id=route_table.id
    )

# 7. Security Groups
alb_sg = ec2.SecurityGroup("alb-sg",
    vpc_id=vpc.id,
    description="Allow HTTP inbound",
    ingress=[{
        "protocol": "tcp",
        "from_port": 80,
        "to_port": 80,
        "cidr_blocks": ["0.0.0.0/0"],
    }],
    egress=[{
        "protocol": "-1",
        "from_port": 0,
        "to_port": 0,
        "cidr_blocks": ["0.0.0.0/0"],
    }]
)

ecs_sg = ec2.SecurityGroup("ecs-sg",
    vpc_id=vpc.id,
    description="Allow traffic from ALB",
    ingress=[{
        "protocol": "tcp",
        "from_port": 5000,
        "to_port": 5000,
        "security_groups": [alb_sg.id],
    }],
    egress=[{
        "protocol": "-1",
        "from_port": 0,
        "to_port": 0,
        "cidr_blocks": ["0.0.0.0/0"],
    }]
)

# 8. Create ALB
alb = lb.LoadBalancer("flask-alb",
    internal=False,
    security_groups=[alb_sg.id],
    subnets=[s.id for s in subnets],
    load_balancer_type="application"
)

target_group = lb.TargetGroup("flask-tg",
    port=5000,
    protocol="HTTP",
    target_type="ip",
    vpc_id=vpc.id
)

listener = lb.Listener("flask-listener",
    load_balancer_arn=alb.arn,
    port=80,
    default_actions=[{
        "type": "forward",
        "target_group_arn": target_group.arn,
    }]
)

# 9. ECS Cluster
cluster = ecs.Cluster("flask-cluster")

# 10. ECR Repo
repo = ecr.Repository("flask-ipsum-repo")

# 11. Get ECR credentials
auth_token = aws.ecr.get_authorization_token(registry_id=repo.registry_id)
decoded = base64.b64decode(auth_token.authorization_token).decode()
password = decoded.split(":")[1]

registry = {
    "server": repo.repository_url,
    "username": auth_token.user_name,
    "password": password,
}

# 12. Build and push Docker image
image = Image("flask-ipsum-image",
    build={
        "context": "./",
        "dockerfile": "Dockerfile",
        "args": {
            "BUILD_DATE": str(time.time()),
        }
    },
    image_name=f"{repo.repository_url}:latest",
    registry=registry
)


# 13. Task Execution Role
task_exec_role = iam.Role("task-exec-role",
    assume_role_policy="""{
        "Version": "2008-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "ecs-tasks.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }"""
)

iam.RolePolicyAttachment("task-exec-policy-attach",
    role=task_exec_role.name,
    policy_arn="arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
)

# 14. ECS Task Definition with env var for AZ
# Add a random suffix to family to force new task definition revision on each deploy
random_suffix = str(random.randint(10000, 99999))

task_definition = ecs.TaskDefinition("flask-task",
    family=f"flask-task-{random_suffix}",
    cpu="256",
    memory="512",
    network_mode="awsvpc",
    requires_compatibilities=["FARGATE"],
    execution_role_arn=task_exec_role.arn,
    container_definitions=image.image_name.apply(get_container_def)
)

# 15. ECS Service
service = ecs.Service("flask-service",
    cluster=cluster.arn,
    desired_count=1,
    launch_type="FARGATE",
    task_definition=task_definition.arn,
    network_configuration={
        "assign_public_ip": True,
        "subnets": [s.id for s in subnets],
        "security_groups": [ecs_sg.id],
    },
    load_balancers=[{
        "target_group_arn": target_group.arn,
        "container_name": "flask-app",
        "container_port": 5000,
    }],
    deployment_controller={
        "type": "ECS"
    },
    opts=pulumi.ResourceOptions(depends_on=[listener])
)

# 16. Export ALB DNS
pulumi.export("alb_dns", alb.dns_name)
