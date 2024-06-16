import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as opensearch from 'aws-cdk-lib/aws-opensearchservice';

export class AOSStack extends cdk.Stack {
  _vpc;
  _securityGroup;
  public readonly endpoint: string;

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Create a VPC
    this._vpc = ec2.Vpc.fromLookup(this, "VPC", {
      isDefault: true,
    });

    // Create a Security Group for OpenSearch
    this._securityGroup = new ec2.SecurityGroup(this, 'GenBIOpenSearchSG', {
      vpc: this._vpc,
      description: 'Allow access to OpenSearch',
      allowAllOutbound: true
    });

    // Allow inbound HTTP and HTTPS traffic
    this._securityGroup.addIngressRule(ec2.Peer.anyIpv4(), ec2.Port.tcp(80), 'Allow HTTP access');
    this._securityGroup.addIngressRule(ec2.Peer.anyIpv4(), ec2.Port.tcp(443), 'Allow HTTPS access');

    // Find subnets in different availability zones
    const subnets = this._vpc.selectSubnets({
      subnetType: ec2.SubnetType.PUBLIC,
    }).subnets;

    if (subnets.length < 3) {
      throw new Error('The VPC must have at least two public subnets in different availability zones.');
    }

    // Create the OpenSearch domain
    const domain = new opensearch.Domain(this, 'GenBIOpenSearchDomain', {
      version: opensearch.EngineVersion.OPENSEARCH_2_9,
      vpc: this._vpc,
      vpcSubnets: [
        { subnets: [subnets[0]] },
        { subnets: [subnets[1]] },
        { subnets: [subnets[2]]}
      ],
      securityGroups: [this._securityGroup],
      capacity: {
        masterNodes: 3,
        dataNodes: 3,
        masterNodeInstanceType: 'm5.large.search',
        dataNodeInstanceType: 'm5.large.search'
      },
      ebs: {
        volumeType: ec2.EbsDeviceVolumeType.GP3,
        volumeSize: 100,
      },
      zoneAwareness: {
        enabled: true,
        availabilityZoneCount: 3,
      },
      nodeToNodeEncryption: true,
      encryptionAtRest: {
        enabled: true
      },
      enforceHttps: true,
      fineGrainedAccessControl: {
        masterUserName: 'master-user',
        masterUserPassword: cdk.SecretValue.unsafePlainText('MasterUserPassword&123'),
      },
      logging: {
        appLogEnabled: true,
        slowSearchLogEnabled: true,
        slowIndexLogEnabled: true,
      }
    });
    this.endpoint = domain.domainEndpoint;
    new cdk.CfnOutput(this, 'AOSDomainEndpoint', {
      value: this.endpoint,
      description: 'The endpoint of the OpenSearch domain'
    });
  }
}

// const app = new cdk.App();
// new AOSStack(app, 'AOSStack', {
//   env: {
//     account: process.env.CDK_DEFAULT_ACCOUNT,
//     region: process.env.CDK_DEFAULT_REGION
//   }
// });
