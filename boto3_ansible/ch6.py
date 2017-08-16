import inspect
import json
import boto3
from ch2 import create_vpc_subnet, create_subnet_name_tag
from ch3 import create_security_group, authorize_ingress_by_ssh_port, create_ec2_instances
from util import create_ec2_client, create_ec2_resource, print_response


def get_availability_zone_at_public_subnet(ec2_resource, subnet_id):
    # https://boto3.readthedocs.io/en/latest/reference/services/ec2.html#subnet
    ec2_subnet = ec2_resource.Subnet(subnet_id)
    return ec2_subnet.availability_zone


def authorize_ingress_by_mysql_port(ec2_resource, security_group_id):
    # https://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.SecurityGroup.authorize_ingress
    security_group = ec2_resource.SecurityGroup(security_group_id)
    response = security_group.authorize_ingress(
        CidrIp='0.0.0.0/0',
        IpProtocol='tcp',
        FromPort=3306,
        ToPort=3306,
    )
    print_response(inspect.getframeinfo(inspect.currentframe())[2], response)


def authorize_ingress_by_icmp_port(ec2_resource, security_group_id):
    # https://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.SecurityGroup.authorize_ingress
    security_group = ec2_resource.SecurityGroup(security_group_id)
    response = security_group.authorize_ingress(
        CidrIp='0.0.0.0/0',
        IpProtocol='icmp',
        FromPort=-1,
        ToPort=-1,
    )
    print_response(inspect.getframeinfo(inspect.currentframe())[2], response)


if __name__ == '__main__':
    session = boto3.Session(profile_name='my-profile')
    # 使用するクライアントとリソースを作成
    client = create_ec2_client(session)
    resource = create_ec2_resource(session)

    # AWSの各IDを取得する
    with open('aws.json', mode='r') as f:
        aws = json.load(f)

    # パブリックサブネットのAvailability Zoneを取得する
    zone = get_availability_zone_at_public_subnet(resource, aws['public_subnet_id'])

    # プライベートサブネットを作る
    subnet = create_vpc_subnet(resource, aws['vpc_id'], zone, '192.168.2.0/24')
    aws['private_subnet_id'] = subnet.subnet_id

    # プライベートサブネットに名前をつける
    create_subnet_name_tag(subnet, 'プライベートサブネット2')

    # セキュリティグループを作成する
    aws['db_security_group_id'] = create_security_group(client, aws['vpc_id'], name='DB-SG2')

    # セキュリティグループでSSHのポートを開ける
    authorize_ingress_by_ssh_port(resource, aws['db_security_group_id'])

    # セキュリティグループでMySQLのポートを開ける
    authorize_ingress_by_mysql_port(resource, aws['db_security_group_id'])

    # EC2を立てる
    instance = create_ec2_instances(
        resource, aws['db_security_group_id'], aws['private_subnet_id'], aws['key_pair_name'],
        is_associate_public_ip=False, private_ip='192.168.2.10', instance_name='DBサーバー2')
    aws['db_instance_id'] = instance.instance_id

    # セキュリティグループでICMPのポートを開ける
    authorize_ingress_by_icmp_port(resource, aws['db_security_group_id'])

    # WebサーバーでもICMPのポートを開ける
    authorize_ingress_by_icmp_port(resource, aws['web_security_group_id'])

    # ここまでのid情報をJSONとして上書き保存
    with open('aws.json', mode='w') as f:
        json.dump(aws, f)
