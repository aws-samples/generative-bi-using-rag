import * as cdk from 'aws-cdk-lib';
import * as rds from 'aws-cdk-lib/aws-rds';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import { Construct } from 'constructs';
import { InstanceClass, InstanceSize, InstanceType, Port, SubnetType, Vpc } from 'aws-cdk-lib/aws-ec2'
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';

interface RDSStackProps extends cdk.StackProps {
  subnets?: ec2.SubnetSelection;
  vpc:ec2.IVpc;
}
// add rds stack
export class RDSStack extends cdk.Stack {
    public readonly endpoint: string;
    public readonly rdsSecurityGroup: ec2.SecurityGroup;
    constructor(scope: Construct, id: string,  props: RDSStackProps) {
        super(scope, id, props);

        const templatedSecret = new secretsmanager.Secret(this, 'GenBIRDSTemplatedSecret', {
            description: 'Templated secret used for RDS password',
            generateSecretString: {
              excludePunctuation: true,
              includeSpace: false,
              generateStringKey: 'password',
              passwordLength: 12,
              secretStringTemplate: JSON.stringify({ username: 'user' })
            },
            removalPolicy: cdk.RemovalPolicy.DESTROY
        });
          
        // Create an RDS instance
        const database = new rds.DatabaseInstance(this, 'Database', {
            engine: rds.DatabaseInstanceEngine.mysql({ version: rds.MysqlEngineVersion.VER_8_0 }),
            instanceType: ec2.InstanceType.of(InstanceClass.T3, InstanceSize.MICRO),
            vpc: props.vpc,
            vpcSubnets: props.subnets || { subnetType: SubnetType.PRIVATE_WITH_EGRESS },
            publiclyAccessible: false,
            databaseName: 'GenBIDB',
            credentials: rds.Credentials.fromSecret(templatedSecret),
        });
        this.endpoint = database.instanceEndpoint.hostname;
        // Output the database endpoint
        new cdk.CfnOutput(this, 'RDSEndpoint', {
            value: database.instanceEndpoint.hostname,
            description: 'The endpoint of the RDS instance',
        });
    }
}