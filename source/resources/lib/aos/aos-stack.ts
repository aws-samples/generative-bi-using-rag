import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as opensearch from 'aws-cdk-lib/aws-opensearchservice';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';

export class AOSStack extends cdk.Stack {
  _vpc;
  _securityGroup;
  public readonly endpoint: string;

  constructor(scope: Construct, id: string, props: cdk.StackProps) {
    super(scope, id, props);

    this._vpc = ec2.Vpc.fromLookup(this, "VPC", {
      isDefault: true,
    });
    // Lookup a VPC
    // this._vpc = props.vpc;

    // Create a Security Group for OpenSearch
    this._securityGroup = new ec2.SecurityGroup(this, 'GenBIOpenSearchSG', {
      vpc: this._vpc,
      description: 'Allow access to OpenSearch',
      allowAllOutbound: true
    });
    const secretName = 'GenBIAOSSecret'; // Add the secret name here
    // const existingSecret = secretsmanager.Secret.fromSecretNameV2(this, 'ExistingSecret', secretName);
    // const templatedSecret = existingSecret || new secretsmanager.Secret(this, 'TemplatedSecret', {
    const templatedSecret = new secretsmanager.Secret(this, 'TemplatedSecret', {
      secretName: secretName,
      description: 'Templated secret used for OpenSearch master user password',
      generateSecretString: {
      excludePunctuation: false,
      includeSpace: false,
      generateStringKey: 'password',
      passwordLength: 12,
      requireEachIncludedType: true,
      secretStringTemplate: JSON.stringify({ username: 'master-user' })
      },
      removalPolicy: cdk.RemovalPolicy.DESTROY
    });

    // Allow inbound HTTP and HTTPS traffic
    this._securityGroup.addIngressRule(ec2.Peer.anyIpv4(), ec2.Port.tcp(80), 'Allow HTTP access');
    this._securityGroup.addIngressRule(ec2.Peer.anyIpv4(), ec2.Port.tcp(443), 'Allow HTTPS access');

    // Find subnets in different availability zones
    const subnets = this._vpc.selectSubnets({
      subnetType: ec2.SubnetType.PUBLIC,
    }).subnets;

    // if (subnets.length < 3) {
    //   throw new Error('The VPC must have at least two public subnets in different availability zones.');
    // }

    // Create the OpenSearch domain
    const domain = new opensearch.Domain(this, 'GenBiOpenSearchDomain', {
      version: opensearch.EngineVersion.OPENSEARCH_2_9,
      vpc: this._vpc,
      securityGroups: [this._securityGroup],
      vpcSubnets: [
        { subnets: [subnets[0]] },
      ],      
      // vpcSubnets: SubnetSelection(one_per_az=True, subnet_type=aws_ec2.SubnetType.PUBLIC),
      capacity: {
        dataNodes: 1,
        dataNodeInstanceType: 'm5.large.search',
        multiAzWithStandbyEnabled: false
      },
      ebs: {
        volumeType: ec2.EbsDeviceVolumeType.GP3,
        volumeSize: 20,
      },
      zoneAwareness: {
        enabled: false
      },
      nodeToNodeEncryption: true,
      encryptionAtRest: {
        enabled: true
      },
      enforceHttps: true,
      fineGrainedAccessControl: {
        masterUserName: 'master-user',
        masterUserPassword: cdk.SecretValue.secretsManager(templatedSecret.secretArn, {
          jsonField: 'password'
        }
        ),
      },
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
