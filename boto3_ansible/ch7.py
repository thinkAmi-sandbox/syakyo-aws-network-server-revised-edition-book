import datetime
import inspect
import json
import boto3
from util import create_ec2_client, create_ec2_resource, print_response


def create_elastic_ip(ec2_client):
    # https://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.Client.allocate_address
    # DomainのvpcはVPC、standardはEC2-Classic向け
    response = ec2_client.allocate_address(Domain='vpc')
    print_response(inspect.getframeinfo(inspect.currentframe())[2], response)
    return response['AllocationId']


def create_nat_gateway(ec2_client, allocation_id, subnet_id):
    # https://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.Client.create_nat_gateway
    response = client.create_nat_gateway(
        AllocationId=allocation_id,
        SubnetId=subnet_id,
    )
    print_response(inspect.getframeinfo(inspect.currentframe())[2], response)
    return response['NatGateway']['NatGatewayId']


def describe_main_route_tables(ec2_client, vpc_id):
    # https://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.Client.describe_route_tables
    response = ec2_client.describe_route_tables(
        Filters=[
            {
                'Name': 'association.main',
                'Values': ['true'],
            },
            {
                'Name': 'vpc-id',
                'Values': [vpc_id],
            }
        ]
    )
    main_route_table_id = response['RouteTables'][0]['RouteTableId']
    print_response(inspect.getframeinfo(inspect.currentframe())[2], main_route_table_id)
    return main_route_table_id


def wait_nat_gateway_available(ec2_client, nat_gateway_id):
    # https://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.Waiter.NatGatewayAvailable
    print(f'NAT Gatewayがavailableになるまで待つ(開始)：{datetime.datetime.now()}')
    waiter = ec2_client.get_waiter('nat_gateway_available')
    response = waiter.wait(
        Filters=[{
            'Name': 'state',
            'Values': ['available']
        }],
        NatGatewayIds=[nat_gateway_id]
    )
    print_response(inspect.getframeinfo(inspect.currentframe())[2], response)
    print(f'NAT Gatewayがavailableになるまで待つ(終了)：{datetime.datetime.now()}')


def create_nat_gateway_route_in_route_table(ec2_resource, route_table_id, nat_gateway_id):
    # https://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.RouteTable.create_route
    route_table = ec2_resource.RouteTable(route_table_id)
    route = route_table.create_route(
        DestinationCidrBlock='0.0.0.0/0',
        NatGatewayId=nat_gateway_id,
    )
    print_response(inspect.getframeinfo(inspect.currentframe())[2], route)
    return route


if __name__ == '__main__':
    session = boto3.Session(profile_name='my-profile')
    # 使用するクライアントとリソースを作成
    client = create_ec2_client(session)
    resource = create_ec2_resource(session)

    # AWSの各IDを取得する
    with open('aws.json', mode='r') as f:
        aws = json.load(f)

    # Elastic IPを取得する
    aws['allocation_id'] = create_elastic_ip(client)

    # パブリックサブネットにNATゲートウェイを置く
    aws['nat_gateway_id'] = create_nat_gateway(client, aws['allocation_id'], aws['public_subnet_id'])

    # NATゲートウェイはすぐに使うことができないため、availableになるまで待つ
    wait_nat_gateway_available(client, aws['nat_gateway_id'])

    # NATゲートウェイのエントリを追加するため、メインのルートテーブルのIDを取得する
    aws['main_route_table_id'] = describe_main_route_tables(client, aws['vpc_id'])

    # VPC領域2でメインのルートテーブルにNATゲートウェイのエントリを追加する
    create_nat_gateway_route_in_route_table(resource, aws['main_route_table_id'], aws['nat_gateway_id'])

    # ここまでのid情報をJSONとして上書き保存
    with open('aws.json', mode='w') as f:
        json.dump(aws, f)
