import * as cdk from 'aws-cdk-lib';
import * as rds from 'aws-cdk-lib/aws-rds';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import { Construct } from 'constructs';
import { InstanceClass, InstanceSize, InstanceType, Port, SubnetType, Vpc } from 'aws-cdk-lib/aws-ec2'
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';

// add rds stack
export class RDSStack extends cdk.Stack {
    _vpc;
    public readonly endpoint: string;
    constructor(scope: Construct, id: string, props?: cdk.StackProps) {
        super(scope, id, props);
        
        this._vpc = ec2.Vpc.fromLookup(this, "VPC", {
            isDefault: true,
        });
        
        const templatedSecret = new secretsmanager.Secret(this, 'TemplatedSecret', {
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
            vpc: this._vpc,
            vpcSubnets: {
                subnetType: ec2.SubnetType.PRIVATE_ISOLATED
            },
            publiclyAccessible: true,
            databaseName: 'GenBIDB',
            credentials: rds.Credentials.fromSecret(templatedSecret),
        });
        this.endpoint = database.instanceEndpoint.hostname;
        // Output the database endpoint
        new cdk.CfnOutput(this, 'RDSEndpoint', {
            value: database.instanceEndpoint.hostname,
        });
    }
}