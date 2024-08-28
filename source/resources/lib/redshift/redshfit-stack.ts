import * as cdk from 'aws-cdk-lib';
import * as redshift from 'aws-cdk-lib/aws-redshift';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import { Construct } from 'constructs';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';

interface RedshiftStackProps extends cdk.StackProps {
  vpc: ec2.IVpc;
  subnets?: ec2.SubnetSelection;
}


export class RedshiftStack extends cdk.Stack {
  public readonly endpoint: string;

  constructor(scope: Construct, id: string, props: RedshiftStackProps) {
    super(scope, id, props);

    // Create a secret for Redshift credentials
    const redshiftSecret = new secretsmanager.Secret(this, 'RedshiftSecret', {
      description: 'Secret for Redshift cluster credentials',
      generateSecretString: {
        secretStringTemplate: JSON.stringify({ username: 'admin' }),
        generateStringKey: 'password',
        excludePunctuation: true,
        includeSpace: false,
        passwordLength: 16,
      },
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    // Create a security group for Redshift
    const redshiftSecurityGroup = new ec2.SecurityGroup(this, 'RedshiftSecurityGroup', {
      vpc: props.vpc,
      description: 'Security group for Redshift cluster',
      allowAllOutbound: true,
    });

    // Allow inbound traffic on port 5439 (default Redshift port)
    redshiftSecurityGroup.addIngressRule(ec2.Peer.anyIpv4(), ec2.Port.tcp(5439), 'Allow Redshift access');

    // Create the Redshift cluster
    const redshiftCluster = new redshift.Cluster(this, 'RedshiftCluster', {
      masterUser: {
        masterUsername: 'admin',
        masterPassword: redshiftSecret.secretValueFromJson('password'),
      },
      vpc: props.vpc,
      vpcSubnets: props.subnets || { subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS },
      securityGroups: [redshiftSecurityGroup],
      clusterType: redshift.ClusterType.SINGLE_NODE,
      nodeType: redshift.NodeType.DC2_LARGE,
      defaultDatabaseName: 'default_db',
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    this.endpoint = redshiftCluster.clusterEndpoint.hostname;

    // Output the Redshift cluster endpoint
    new cdk.CfnOutput(this, 'RedshiftEndpoint', {
      value: redshiftCluster.clusterEndpoint.hostname,
      description: 'The endpoint of the Redshift cluster',
    });
  }
}