
import { NestedStack, StackProps } from 'aws-cdk-lib';
import { Construct } from 'constructs';

import * as ec2 from "aws-cdk-lib/aws-ec2";
import * as iam from "aws-cdk-lib/aws-iam";
import { Asset } from 'aws-cdk-lib/aws-s3-assets';

import path from "path";

export class Ec2Stack extends NestedStack {
  _vpc;
  _securityGroup;
  _instanceId;
  _dnsName;
  _publicIP;

  constructor(scope: Construct, id: string, props: StackProps = {}) {
    super(scope, id, props);
    this._vpc = ec2.Vpc.fromLookup(this, "VPC", {
      isDefault: true,
    });

    this._securityGroup = new ec2.SecurityGroup(this, 'GenBiSecurityGroup', {
      vpc: this._vpc,
      description: 'Genaratie Bi Security Group'
    });

    this._securityGroup.addIngressRule(ec2.Peer.anyIpv4(), ec2.Port.tcp(22), 'Allow SSH Access')
    this._securityGroup.addIngressRule(ec2.Peer.anyIpv4(), ec2.Port.tcp(80), 'Allow HTTP Access')
    this._securityGroup.addIngressRule(ec2.Peer.anyIpv4(), ec2.Port.tcp(5000), 'Allow API Access')
    this._securityGroup.addIngressRule(this._securityGroup, ec2.Port.allTraffic(), 'Allow Self Access')

    const role = new iam.Role(this, 'ec2Role', {
      assumedBy: new iam.ServicePrincipal('ec2.amazonaws.com')
    })

    // Add bedrock:* permissions to the role
    role.addToPolicy(new iam.PolicyStatement({
      actions: ['bedrock:*'],
      resources: ['*'],
    }));

    // Add dynamodb:* permissions to the role
    role.addToPolicy(new iam.PolicyStatement({
      actions: ['dynamodb:*'],
      resources: ['*'],
    }));

    const ami = new ec2.AmazonLinux2023ImageSsmParameter({
      kernel: ec2.AmazonLinux2023Kernel.KERNEL_6_1,
    })

    // Create the instance using the Security Group, AMI, and KeyPair defined in the VPC created
    // TODO: Change to M5 instance type
    const ec2Instance = new ec2.Instance(this, 'GenBiInstance', {
      vpc: this._vpc,
      instanceType: ec2.InstanceType.of(ec2.InstanceClass.M5, ec2.InstanceSize.XLARGE),
      machineImage: ami,
      securityGroup: this._securityGroup,
      vpcSubnets: { subnetType: ec2.SubnetType.PUBLIC, },
      role: role,
      blockDevices: [{
        deviceName: '/dev/xvda',
        volume: ec2.BlockDeviceVolume.ebs(100),  // 100 GB root volume
      }],
    });

    let installDockerAsset;
    let setupAppAsset;
    if (props.env?.region === "cn-north-1" || props.env?.region === "cn-northwest-1") {
      installDockerAsset = new Asset(this, 'InstallDockerAsset', { path: path.join(__dirname, 'cn_user_data/install_docker.sh') });
      setupAppAsset = new Asset(this, 'SetupAppAsset', { path: path.join(__dirname, 'cn_user_data/setup_app.sh') });
    } else {
      installDockerAsset = new Asset(this, 'InstallDockerAsset', { path: path.join(__dirname, 'user_data/install_docker.sh') });
      setupAppAsset = new Asset(this, 'SetupAppAsset', { path: path.join(__dirname, 'user_data/setup_app.sh') });
    }
    const installDockerLocalPath = ec2Instance.userData.addS3DownloadCommand({
      bucket: installDockerAsset.bucket,
      bucketKey: installDockerAsset.s3ObjectKey,
    });

    const setupAppLocalPath = ec2Instance.userData.addS3DownloadCommand({
      bucket: setupAppAsset.bucket,
      bucketKey: setupAppAsset.s3ObjectKey,
    });

    ec2Instance.userData.addExecuteFileCommand({
      filePath: installDockerLocalPath,
    });
    ec2Instance.userData.addExecuteFileCommand({
      filePath: setupAppLocalPath
    });
    installDockerAsset.grantRead(ec2Instance.role);
    setupAppAsset.grantRead(ec2Instance.role);

    this._instanceId = ec2Instance.instanceId;
    this._dnsName = ec2Instance.instancePublicDnsName;
    this._publicIP = ec2Instance.instancePublicIp;
  }
}