# syakyo-aws-network-server-revised-edition-book

## Tested environment

- Mac OS X 10.11.6
- Python 3.6.2
- boto3 1.4.5
- ansible 2.3.2.0

　  
## Usage boto3 & ansible files



```
$ pwd
/path/to/boto3_ansible

# Chapter2 
$ python ch2.py

# Chapter3
$ python ch3.py

# rename
$ mv ssh_config.example ssh_config

# update ssh_config file
## HostName: your EC2's public ip address

# Chapter4
$ python ch4.py
$ ansible-playbook -i hosts ch4_apache.yml

# Chapter6
$ python ch6.py
$ ansible-playbook -i hosts ch6_scp_to_web.yml

# Chapter7
$ python ch7.py

# clear all chapter items
$ python clear_all.py
```

　  
## Related Blog (Written in Japanese)

- [「Amazon Web Services 基礎からのネットワーク&サーバー構築 改訂版」をboto3とAnsibleで写経してみた - メモ的な思考的な](http://thinkami.hatenablog.com/entry/2017/08/17/230736)
