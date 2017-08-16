import datetime
import inspect
import json
import os
import boto3
from util import create_ec2_client, create_ec2_resource, print_response

IMAGE_ID = 'ami-3bd3c45c'
KEY_PAIR_NAME = 'syakyo_aws_network_server2'
KEY_PAIR_FILE = f'{KEY_PAIR_NAME}.pem'


def describe_images(ec2_client):
    # https://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.Client.describe_images
    response = ec2_client.describe_images(
        Filters=[
            {
                'Name': 'image-id',
                'Values': [IMAGE_ID]
            },
        ]
    )
    return response['Images']


def create_key_pair(ec2_client):
    # https://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.Client.create_key_pair
    # キーペアを作成していない場合はキーペアを作成する
    if not os.path.exists(KEY_PAIR_FILE):
        response = ec2_client.create_key_pair(KeyName=KEY_PAIR_NAME)
        print(inspect.getframeinfo(inspect.currentframe())[2], response['KeyName'])
        with open(KEY_PAIR_FILE, mode='w') as f:
            f.write(response['KeyMaterial'])

    return KEY_PAIR_NAME


def create_security_group(ec2_client, vpc_id, name):
    # https://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.Client.create_security_group
    response = ec2_client.create_security_group(
        Description=name,
        GroupName=name,
        VpcId=vpc_id,
    )
    print_response(inspect.getframeinfo(inspect.currentframe())[2], response)
    return response['GroupId']


def authorize_ingress_by_ssh_port(ec2_resource, security_group_id):
    # https://boto3.readthedocs.io/en/latest/reference/services/ec2.html#securitygroup
    # https://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.SecurityGroup.authorize_ingress
    security_group = ec2_resource.SecurityGroup(security_group_id)
    response = security_group.authorize_ingress(
        CidrIp='0.0.0.0/0',
        IpProtocol='tcp',
        # ポートは22だけ許可したいので、From/Toともに22のみとする
        FromPort=22,
        ToPort=22,
    )
    print_response(inspect.getframeinfo(inspect.currentframe())[2], response)


def create_ec2_instances(
        ec2_resource, security_group_id, subnet_id, key_pair_name, is_associate_public_ip, private_ip, instance_name):
    # https://boto3.readthedocs.io/en/latest/reference/services/ec2.html#service-resource
    # https://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.ServiceResource.create_instances
    response = ec2_resource.create_instances(
        ImageId=IMAGE_ID,
        # 無料枠はt2.micro
        InstanceType='t2.micro',
        # 事前に作ったキー名を指定
        KeyName=key_pair_name,
        # インスタンス数は、最大・最小とも1にする
        MaxCount=1,
        MinCount=1,
        # モニタリングはデフォルト = Cloud Watchは使わないはず
        # Monitoring={'Enabled': False},
        # サブネットにavailability zone が結びついてるので、明示的なセットはいらないかも
        # Placement={'AvailabilityZone': availability_zone},
        # セキュリティグループIDやサブネットIDはNetworkInterfacesでセット(詳細は以下)
        # SecurityGroupIds=[security_group_id],
        # SubnetId=subnet_id,
        NetworkInterfaces=[{
            # 自動割り当てパブリックIP
            'AssociatePublicIpAddress': is_associate_public_ip,
            # デバイスインタフェースは1つだけなので、最初のものを使う
            'DeviceIndex': 0,
            # セキュリティグループIDは、NetworkInterfacesの方で割り当てる
            # インスタンスの方で割り当てると以下のエラー：
            # Network interfaces and an instance-level security groups may not be specified on the same request
            'Groups': [security_group_id],
            # プライベートIPアドレス
            'PrivateIpAddress': private_ip,
            # サブネットIDも、NetworkInterfacesの方で割り当てる
            # インスタンスの方で割り当てると以下のエラー：
            # Network interfaces and an instance-level subnet ID may not be specified on the same request
            'SubnetId': subnet_id,
        }],
        TagSpecifications=[{
            'ResourceType': 'instance',
            'Tags': [{
                'Key': 'Name',
                'Value': instance_name,
            }]
        }],
    )
    print_response(inspect.getframeinfo(inspect.currentframe())[2], response)

    # EC2インスタンスは1つだけ生成しているので、そのインスタンスを戻り値にする
    return response[0]


def wait(ec2_client, ec2_instance):
    # https://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.Instance.wait_until_running
    print(f'起動待ち: {datetime.datetime.now()}')
    ec2_instance.wait_until_running()
    print(f'起動しました：{datetime.datetime.now()}')

    # この時点ではパブリックIPアドレスは取得できない
    print(ec2_instance.public_ip_address)
    # => None
    print(ec2_instance.network_interfaces_attribute)
    # => パブリックIPアドレスのエントリがない

    # OKまで待つ
    waiter = ec2_client.get_waiter('instance_status_ok')
    waiter.wait()
    print(f'OKまで待ちました：{datetime.datetime.now()}')
    print(ec2_instance.network_interfaces_attribute)


if __name__ == '__main__':
    session = boto3.Session(profile_name='my-profile')
    # 使用するクライアントとリソースを作成
    client = create_ec2_client(session)
    resource = create_ec2_resource(session)

    # 無料枠のイメージを事前に調べ上げて、定数IMAGE_IDに入れておく
    # IMAGE_IDが存在しない場合、処理を終える
    ec2_images = describe_images(client)

    # AWSの各IDを取得する
    with open('aws.json', mode='r') as f:
        aws = json.load(f)

    if len(ec2_images) == 0:
        print('該当するAMIがなかったため、処理を終了します。')

    # キーペアを作成する
    aws['key_pair_name'] = create_key_pair(client)

    # キーペアのパーミッションを変更
    # modeは8進数表記がわかりやすい：Python3からはprefixが`0o`となった
    os.chmod(KEY_PAIR_FILE, mode=0o400)

    # セキュリティグループを作成する
    aws['web_security_group_id'] = create_security_group(client, aws['vpc_id'], name='WEB-SG2')

    # セキュリティグループでSSHのポートを開ける
    authorize_ingress_by_ssh_port(resource, aws['web_security_group_id'])

    # EC2を立てる
    instance = create_ec2_instances(
        resource, aws['web_security_group_id'], aws['public_subnet_id'], aws['key_pair_name'],
        is_associate_public_ip=True, private_ip='192.168.1.10', instance_name='Webサーバー2')
    aws['web_instance_id'] = instance.instance_id

    # running & InstanceStatusOkになるまで待つ
    wait(client, instance)

    # ここまでのid情報をJSONとして上書き保存
    with open('aws.json', mode='w') as f:
        json.dump(aws, f)
