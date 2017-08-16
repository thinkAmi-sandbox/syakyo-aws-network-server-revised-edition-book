def create_ec2_client(session):
    return session.client('ec2', region_name='ap-northeast-1')


def create_ec2_resource(session):
    return session.resource('ec2', region_name='ap-northeast-1')


def print_response(function_name, response):
    line = '-' * 20
    print(f'{line}\n{function_name}\n{line}\n{response}\n')
