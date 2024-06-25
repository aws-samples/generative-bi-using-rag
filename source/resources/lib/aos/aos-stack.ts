import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as opensearch from 'aws-cdk-lib/aws-opensearchservice';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import { AnyPrincipal, Effect, PolicyStatement } from "aws-cdk-lib/aws-iam";

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
    this._securityGroup.applyRemovalPolicy(cdk.RemovalPolicy.DESTROY);

    const secretName = 'opensearch-master-user'; // Add the secret name here
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
      subnetType: ec2.SubnetType.PRIVATE_ISOLATED,
    }).subnets;

    // Create the OpenSearch domain
    const domain = new opensearch.Domain(this, 'GenBiOpenSearchDomain', {
      version: opensearch.EngineVersion.OPENSEARCH_2_9,
      vpc: this._vpc,
      securityGroups: [this._securityGroup],
      accessPolicies: [new PolicyStatement({
          effect: Effect.ALLOW,
          principals: [new AnyPrincipal()],
          actions: ["es:*"],
          resources: [`arn:aws:es:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:domain/*`]
      })]
      ,
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
        }),
      },
    });
    domain.applyRemovalPolicy(cdk.RemovalPolicy.DESTROY);
    this.endpoint = domain.domainEndpoint.toString();
    
    const hostSecretName = 'opensearch-host-url'; // Add the secret name here
    const hostSecret = new secretsmanager.Secret(this, 'HostSecret', {
      secretName: hostSecretName,
      generateSecretString: {
        secretStringTemplate: JSON.stringify({host: this.endpoint}),
        generateStringKey: 'password', // Specify the key under which the secret will be stored
      },
    });

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
