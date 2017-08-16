import inspect
import json
import boto3
from util import create_ec2_client, create_ec2_resource, print_response


def authorize_ingress_by_http_port(ec2_resource, security_group_id):
    # https://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.SecurityGroup.authorize_ingress
    security_group = ec2_resource.SecurityGroup(security_group_id)
    response = security_group.authorize_ingress(
        CidrIp='0.0.0.0/0',
        IpProtocol='tcp',
        FromPort=80,
        ToPort=80,
    )
    print_response(inspect.getframeinfo(inspect.currentframe())[2], response)


def modify_vpc_attribute(ec2_client, vpc_id):
    # https://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.Client.modify_vpc_attribute
    response = ec2_client.modify_vpc_attribute(
        EnableDnsHostnames={'Value': True},
        VpcId=vpc_id,
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

    # セキュリティグループでHTTPのポートを開ける
    authorize_ingress_by_http_port(resource, aws['web_security_group_id'])

    # 「DNSホスト名の編集」を実行する
    modify_vpc_attribute(client, aws['vpc_id'])
