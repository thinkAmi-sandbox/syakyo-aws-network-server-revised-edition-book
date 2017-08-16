import inspect
import json
import boto3
from util import create_ec2_client, create_ec2_resource, print_response


def create_vpc(ec2_client):
    # https://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.Client.create_vpc
    response = ec2_client.create_vpc(
        CidrBlock='192.168.0.0/16',
        AmazonProvidedIpv6CidrBlock=False,
    )
    vpc_id = response['Vpc']['VpcId']
    print_response(inspect.getframeinfo(inspect.currentframe())[2], vpc_id)
    return vpc_id


def add_vpc_name_tag(ec2_resource, vpc_id):
    # https://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.Vpc.create_tags
    vpc = ec2_resource.Vpc(vpc_id)
    tag = vpc.create_tags(
        Tags=[
            {
                'Key': 'Name',
                'Value': 'VPC領域2'
            },
        ]
    )
    print_response(inspect.getframeinfo(inspect.currentframe())[2], tag)


def describe_vpc(ec2_client):
    # https://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.Client.describe_vpcs
    # VPC名でフィルタ
    response = ec2_client.describe_vpcs(
        Filters=[
            {
                'Name': 'tag:Name',
                'Values': [
                    'VPC領域',
                ]
            }
        ]
    )
    print_response(inspect.getframeinfo(inspect.currentframe())[2], response)


def describe_availability_zones(ec2_client):
    # https://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.Client.describe_availability_zones
    response = ec2_client.describe_availability_zones(
        Filters=[{
            'Name': 'state',
            'Values': ['available'],
        }]
    )
    print_response(inspect.getframeinfo(inspect.currentframe())[2], response)
    return response


def create_vpc_subnet(ec2_resource, vpc_id, availability_zone, cidr_block):
    # clientとresourceのどちらでもできるが、resourceのほうがオブジェクトが返ってきて扱いやすい
    # https://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.Client.create_subnet
    # https://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.Vpc.create_subnet
    vpc = ec2_resource.Vpc(vpc_id)
    response = vpc.create_subnet(
        AvailabilityZone=availability_zone,
        CidrBlock=cidr_block,
    )
    print_response(inspect.getframeinfo(inspect.currentframe())[2], response)
    # https://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.Subnet
    return response


def create_subnet_name_tag(ec2_subnet, subnet_name):
    # https://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.Subnet.create_tags
    tag = ec2_subnet.create_tags(
        Tags=[{
            'Key': 'Name',
            'Value': subnet_name,
        }]
    )
    print_response(inspect.getframeinfo(inspect.currentframe())[2], tag)


def create_internet_gateway(ec2_client):
    # https://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.Client.create_internet_gateway
    response = ec2_client.create_internet_gateway()
    print_response(inspect.getframeinfo(inspect.currentframe())[2], response)
    return response['InternetGateway']['InternetGatewayId']


def create_internet_gateway_name_tag(ec2_resource, internet_gateway_id):
    # https://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.InternetGateway.create_tags
    internet_gateway = ec2_resource.InternetGateway(internet_gateway_id)
    tags = internet_gateway.create_tags(
        Tags=[{
            'Key': 'Name',
            'Value': 'インターネットゲートウェイ2',
        }]
    )
    print_response(inspect.getframeinfo(inspect.currentframe())[2], tags)


def attach_internet_gateway_to_vpc(ec2_resource, internet_gateway_id, vpc_id):
    # clientとresourceのどちらでもできるが、resourceのほうがオブジェクトが返ってきて扱いやすい
    # https://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.Client.attach_internet_gateway
    # https://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.InternetGateway.attach_to_vpc
    internet_gateway = ec2_resource.InternetGateway(internet_gateway_id)
    response = internet_gateway.attach_to_vpc(
        VpcId=vpc_id,
    )
    print_response(inspect.getframeinfo(inspect.currentframe())[2], response)
    return response


def create_route_table(ec2_client, vpc_id):
    # https://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.Client.create_route_table
    response = ec2_client.create_route_table(VpcId=vpc_id)
    route_table_id = response['RouteTable']['RouteTableId']
    print_response(inspect.getframeinfo(inspect.currentframe())[2], route_table_id)
    return route_table_id


def create_route_table_tag_name(ec2_resource, route_table_id):
    # https://boto3.readthedocs.io/en/latest/reference/services/ec2.html#routetable
    route_table = ec2_resource.RouteTable(route_table_id)
    # https://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.RouteTable.create_tags
    tag = route_table.create_tags(
        Tags=[{
            'Key': 'Name',
            'Value': 'パブリックルートテーブル2',
        }]
    )
    print_response(inspect.getframeinfo(inspect.currentframe())[2], tag)


def associate_route_table_with_subnet(ec2_resource, route_table_id, subnet_id):
    # clientとresourceのどちらでもできるが、resourceのほうがオブジェクトが返ってきて扱いやすい
    # https://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.Client.associate_route_table
    # https://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.RouteTable.associate_with_subnet
    route_table = ec2_resource.RouteTable(route_table_id)
    route_table_association = route_table.associate_with_subnet(SubnetId=subnet_id)
    print_response(inspect.getframeinfo(inspect.currentframe())[2], route_table_association)
    return route_table_association.route_table_association_id


def create_route_in_route_table(ec2_resource, route_table_id, internet_gateway_id):
    # https://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.RouteTable.create_route
    route_table = ec2_resource.RouteTable(route_table_id)
    route = route_table.create_route(
        DestinationCidrBlock='0.0.0.0/0',
        GatewayId=internet_gateway_id,
    )
    print_response(inspect.getframeinfo(inspect.currentframe())[2], route)


def describe_route_tables(ec2_client):
    # https://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.Client.describe_route_tables
    response = ec2_client.describe_route_tables()
    print_response(inspect.getframeinfo(inspect.currentframe())[2], response)


if __name__ == '__main__':
    aws = {}
    # profileを使い分ける場合には、profileをセット
    session = boto3.Session(profile_name='my-profile')
    # 使用するクライアントとリソースを作成
    client = create_ec2_client(session)
    resource = create_ec2_resource(session)

    # VPCの作成と確認
    aws['vpc_id'] = create_vpc(client)
    add_vpc_name_tag(resource, aws['vpc_id'])
    describe_vpc(client)

    # サブネットの作成
    # アベイラビリティゾーンの確認
    zones = describe_availability_zones(client)
    # 最初のアベイラビリティゾーンを使用するアベイラビリティゾーンとする
    first_zone = zones['AvailabilityZones'][0]['ZoneName']
    print_response('first availability zone', first_zone)
    subnet = create_vpc_subnet(resource, aws['vpc_id'], first_zone, '192.168.1.0/24')
    aws['public_subnet_id'] = subnet.subnet_id
    # サブネットの名前タグを追加
    create_subnet_name_tag(subnet, 'パブリックサブネット2')

    # インターネットゲートウェイの作成
    aws['internet_gateway_id'] = create_internet_gateway(client)
    # インターネットゲートウェイの名前をつける
    create_internet_gateway_name_tag(resource, aws['internet_gateway_id'])
    # インターネットゲートウェイをVPC領域に結びつける
    attach_internet_gateway_to_vpc(resource, aws['internet_gateway_id'], aws['vpc_id'])

    # ルートテーブルの設定
    # ルートテーブルの作成
    aws['public_route_table_id'] = create_route_table(client, aws['vpc_id'])
    # ルートテーブルにタグを設定
    create_route_table_tag_name(resource, aws['public_route_table_id'])
    # ルートテーブルをサブネットに割り当てる
    aws['public_route_table_association_id'] = associate_route_table_with_subnet(
        resource, aws['public_route_table_id'], aws['public_subnet_id'])
    # デフォルトゲートウェイをインターネットゲートウェイに割り当てる
    create_route_in_route_table(resource, aws['public_route_table_id'], aws['internet_gateway_id'])
    # ルートテーブルの確認
    describe_route_tables(client)

    # ここまでのid情報をJSONとして保存
    with open('aws.json', mode='w') as f:
        json.dump(aws, f)
