import pulumi
import pulumi_aws as aws
from pulumi_aws import ec2, ecs, iam, ecr, cloudwatch, amp
from pulumi_docker import Image
import base64
import json
import os

region = aws.get_region().name

# 1. VPC
vpc = ec2.Vpc("vpc", cidr_block="10.0.0.0/16")

# 2. Public Subnet in one AZ
subnet = ec2.Subnet("subnet",
    vpc_id=vpc.id,
    cidr_block="10.0.1.0/24",
    map_public_ip_on_launch=True,
    availability_zone=aws.get_availability_zones().names[0]
)

# 3. Internet Gateway + Route Table
igw = ec2.InternetGateway("igw", vpc_id=vpc.id)
rt = ec2.RouteTable("rt", vpc_id=vpc.id,
    routes=[{"cidr_block": "0.0.0.0/0", "gateway_id": igw.id}]
)
ec2.RouteTableAssociation("rta", subnet_id=subnet.id, route_table_id=rt.id)

# 4. Security Group (open port 5000)
sg = ec2.SecurityGroup("flask-sg", vpc_id=vpc.id,
    ingress=[{"protocol": "tcp", "from_port": 5000, "to_port": 5000, "cidr_blocks": ["0.0.0.0/0"]}],
    egress=[{"protocol": "-1", "from_port": 0, "to_port": 0, "cidr_blocks": ["0.0.0.0/0"]}]
)

# 5. ECS Cluster
cluster = ecs.Cluster("cluster")

# 6. ECR + Docker Image
image_tag = os.getenv("IMAGE_TAG", "latest")
repo = ecr.Repository("repo")
auth = aws.ecr.get_authorization_token()
decoded = base64.b64decode(auth.authorization_token).decode()
password = decoded.split(":")[1]
registry = {
    "server": repo.repository_url,
    "username": auth.user_name,
    "password": password
}
image = Image("flask-image",
    build={"context": "./"},
    image_name=repo.repository_url.apply(lambda url: f"{url}:{image_tag}"),
    registry=registry
)

# 7. CloudWatch Log Group
log_group = cloudwatch.LogGroup("log-group", retention_in_days=1)

# 8. IAM Role for ECS
role = iam.Role("task-exec-role", assume_role_policy="""{
    "Version": "2008-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Principal": {"Service": "ecs-tasks.amazonaws.com"},
        "Action": "sts:AssumeRole"
    }]
}""")
iam.RolePolicyAttachment("policy-attach", role=role.name,
    policy_arn="arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
)

# 9. ECS Task Definition
container_def = pulumi.Output.all(image.image_name, log_group.name, subnet.availability_zone).apply(
    lambda args: json.dumps([{
        "name": "flask",
        "image": args[0],
        "portMappings": [{"containerPort": 5000}],
        "environment": [
            {"name": "TASK_AZ", "value": args[2]}
        ],
        "logConfiguration": {
            "logDriver": "awslogs",
            "options": {
                "awslogs-group": args[1],
                "awslogs-region": region,
                "awslogs-stream-prefix": "flask"
            }
        }
    }])
)

task_def = ecs.TaskDefinition("task",
    family="flask-task",
    cpu="256",
    memory="512",
    network_mode="awsvpc",
    requires_compatibilities=["FARGATE"],
    execution_role_arn=role.arn,
    container_definitions=container_def
)

# 10. ECS Service
service = ecs.Service("service",
    cluster=cluster.arn,
    desired_count=1,
    launch_type="FARGATE",
    task_definition=task_def.arn,
    network_configuration={
        "assignPublicIp": True,
        "subnets": [subnet.id],
        "security_groups": [sg.id],
    }
)

# 11. AMP Workspace
workspace = amp.Workspace("prometheus-workspace",
    alias="flask-monitoring"
)

# IAM Role for AMP (future use)
scrape_role = iam.Role("amp-scrape-role", assume_role_policy=json.dumps({
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Principal": {"Service": "aps.amazonaws.com"},
        "Action": "sts:AssumeRole"
    }]
}))
iam.RolePolicyAttachment("amp-scrape-policy",
    role=scrape_role.name,
    policy_arn="arn:aws:iam::aws:policy/AmazonPrometheusRemoteWriteAccess"
)

# Export the ECR repo URL
#pulumi.export("ecr_repo_url", repo.repository_url)
pulumi.export("flask_url", service.id)
pulumi.export("amp_workspace_id", workspace.id)
