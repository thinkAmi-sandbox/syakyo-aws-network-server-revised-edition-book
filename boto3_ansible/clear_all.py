import inspect
import json
import os
import boto3
from ch3 import KEY_PAIR_FILE
from clear_ch2 import delete_each_vpc_items
from util import create_ec2_client, create_ec2_resource, print_response


def delete_route_from_main_route_table(ec2_client, main_route_table_id):
    # https://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.Client.delete_route
    response = ec2_client.delete_route(
        DestinationCidrBlock='0.0.0.0/0',
        RouteTableId=main_route_table_id,
    )
    print_response(inspect.getframeinfo(inspect.currentframe())[2], response)


def delete_nat_gateway(ec2_client, nat_gateway_id):
    # https://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.Client.delete_nat_gateway
    response = ec2_client.delete_nat_gateway(NatGatewayId=nat_gateway_id)
    print_response(inspect.getframeinfo(inspect.currentframe())[2], response)


def delete_elastic_ip(ec2_client, allocation_id):
    # https://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.Client.release_address
    response = ec2_client.release_address(AllocationId=allocation_id)
    print_response(inspect.getframeinfo(inspect.currentframe())[2], response)


def terminate_instances_with_wait(ec2_client, instance_id):
    # https://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.Client.terminate_instances
    response = ec2_client.terminate_instances(InstanceIds=[instance_id])
    print_response(inspect.getframeinfo(inspect.currentframe())[2], response)

    # インスタンスが削除されるのを待つ
    # https://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.Waiter.InstanceTerminated
    waiter = ec2_client.get_waiter('instance_terminated')
    waiter.wait(
        Filters=[{
            'Name': 'instance-state-name',
            'Values': ['terminated'],
        }],
        InstanceIds=[instance_id],
    )


def delete_security_group(ec2_client, group_id):
    # https://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.Client.delete_security_group
    response = ec2_client.delete_security_group(GroupId=group_id)
    print_response(inspect.getframeinfo(inspect.currentframe())[2], response)


def delete_subnet(ec2_client, subnet_id):
    # https://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.Client.delete_subnet
    response = ec2_client.delete_subnet(SubnetId=subnet_id)
    print_response(inspect.getframeinfo(inspect.currentframe())[2], response)


def delete_key_pair(ec2_client, key_pair_name):
    # https://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.Client.delete_key_pair
    response = ec2_client.delete_key_pair(KeyName=key_pair_name)
    print_response(inspect.getframeinfo(inspect.currentframe())[2], response)


if __name__ == '__main__':
    # Profileをロード
    session = boto3.Session(profile_name='my-profile')
    # クライアントとリソースを作っておく
    client = create_ec2_client(session)
    resource = create_ec2_resource(session)
    # AWSの各種IDをロード
    with open('aws.json', mode='r') as f:
        aws = json.load(f)

    # --- Chapter 7 --->
    # VPC領域2のメインのルートテーブルからNATゲートウェイのエントリを削除する
    delete_route_from_main_route_table(client, aws['main_route_table_id'])

    # パブリックサブネットからNATゲートウェイを削除する
    delete_nat_gateway(client, aws['nat_gateway_id'])

    # Elastic IPを削除する
    delete_elastic_ip(client, aws['allocation_id'])

    # --- Chapter 6 --->
    # DBサーバーのEC2インスタンスを削除する
    terminate_instances_with_wait(client, aws['db_instance_id'])

    # DBサーバーのセキュリティグループを削除する
    delete_security_group(client, aws['db_security_group_id'])

    # プライベートサブネットを削除する
    delete_subnet(client, aws['private_subnet_id'])

    # Chapter4では、IDがあるようなものを作成していないので、作業を省略

    # --- Chapter 3 --->
    # WebサーバーのEC2インスタンスを削除する
    terminate_instances_with_wait(client, aws['web_instance_id'])

    # Webサーバーのセキュリティグループを削除する
    delete_security_group(client, aws['web_security_group_id'])

    # キーペアを削除する
    delete_key_pair(client, aws['key_pair_name'])

    # キーペアファイルを削除する
    os.remove(KEY_PAIR_FILE)

    # --- Chapter 2 --->
    # GUIではVPCを削除するとそれぞれのオブジェクトも自動的に削除されるが、boto3だとエラーで削除できない
    # botocore.exceptions.ClientError: An error occurred (DependencyViolation) when calling the DeleteVpc operation:
    # The vpc 'vpc-a781dac3' has dependencies and cannot be deleted.
    # delete_vpc(client, aws_keys['vpc_id'])
    # それぞれのオブジェクトを、作成したのとは逆順に削除する
    delete_each_vpc_items(client, aws)


