import boto3
import json
from util import create_ec2_client, create_ec2_resource


def delete_route_from_route_table(ec2_client, route_table_id):
    # https://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.Client.delete_route
    response = ec2_client.delete_route(
        DestinationCidrBlock='0.0.0.0/0',
        RouteTableId=route_table_id,
    )
    print(response)


def disassociate_route_table(ec2_client, route_table_association_id):
    # https://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.Client.disassociate_route_table
    response = ec2_client.disassociate_route_table(AssociationId=route_table_association_id)
    print(response)


def delete_route_table(ec2_client, route_table_id):
    # https://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.Client.delete_route_table
    response = ec2_client.delete_route_table(RouteTableId=route_table_id)
    print(response)


def detach_internet_gateway_from_vpc(ec2_client, internet_gateway_id, vpc_id):
    # https://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.Client.detach_internet_gateway
    response = ec2_client.detach_internet_gateway(
        InternetGatewayId=internet_gateway_id,
        VpcId=vpc_id,
    )
    print(response)


def delete_internet_gateway(ec2_client, internet_gateway_id):
    # https://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.Client.delete_internet_gateway
    response = ec2_client.delete_internet_gateway(InternetGatewayId=internet_gateway_id)
    print(response)


def delete_subnet(ec2_client, subnet_id):
    # https://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.Client.delete_subnet
    response = ec2_client.delete_subnet(SubnetId=subnet_id)
    print(response)


def delete_vpc(ec2_client, vpc_id):
    # https://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.Client.delete_vpc
    response = ec2_client.delete_vpc(VpcId=vpc_id)
    print(response)


def delete_each_vpc_items(ec2_client, aws):
    # 逆順に解放していく
    # デフォルトゲートウェイからインターネットゲートウェイを削除
    delete_route_from_route_table(ec2_client, aws['public_route_table_id'])
    # ルートテーブルとサブネットの関連付けを削除
    disassociate_route_table(ec2_client, aws['public_route_table_association_id'])
    # ルートテーブルの削除
    delete_route_table(ec2_client, aws['public_route_table_id'])

    # インターネットゲートウェイの削除
    # インターネットゲートウェイをVPC領域から削除
    detach_internet_gateway_from_vpc(ec2_client, aws['internet_gateway_id'], aws['vpc_id'])
    # インターネットゲートウェイの削除
    delete_internet_gateway(ec2_client, aws['internet_gateway_id'])

    # サブネットの削除
    delete_subnet(ec2_client, aws['public_subnet_id'])

    # VPC領域の削除
    delete_vpc(client, aws_keys['vpc_id'])


if __name__ == '__main__':
    # Profileをロード
    session = boto3.Session(profile_name='my-profile')
    # クライアントとリソースを作っておく
    client = create_ec2_client(session)
    resource = create_ec2_resource(session)
    # AWSの各種IDをロード
    with open('aws.json', mode='r') as f:
        aws_keys = json.load(f)

    # それぞれのオブジェクトを、作成したのとは逆順に削除する場合
    delete_each_vpc_items(client, aws_keys)

    # GUIではVPCを削除するとそれぞれのオブジェクトも自動的に削除されるが、boto3だとエラーで削除できない
    # botocore.exceptions.ClientError: An error occurred (DependencyViolation) when calling the DeleteVpc operation:
    # The vpc 'vpc-a781dac3' has dependencies and cannot be deleted.
    # delete_vpc(client, aws_keys['vpc_id'])


