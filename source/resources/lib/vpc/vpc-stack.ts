import * as cdk from 'aws-cdk-lib';
import {Construct} from 'constructs';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
interface VPCStackProps extends cdk.StackProps {
    existing_vpc_id?: string;
}

export class VPCStack extends cdk.Stack {
    public readonly vpc: ec2.IVpc;
    public readonly publicSubnets: ec2.ISubnet[];

    constructor(scope: Construct, id: string, props: VPCStackProps) {
        super(scope, id, props);
        // Create a VPC
        if (props.existing_vpc_id) {
            this.vpc = ec2.Vpc.fromLookup(this, 'GenBIVpc', {
                vpcId: props.existing_vpc_id,
            });
        } else{
            this.vpc = new ec2.Vpc(this, 'GenBIVpc', {
            maxAzs: 3, // Default is all AZs in the region
            natGateways: 1,
            subnetConfiguration: [
                {
                    cidrMask: 24,
                    name: 'public-subnet',
                    subnetType: ec2.SubnetType.PUBLIC,
                },
                {
                    cidrMask: 24,
                    name: 'private-subnet',
                    subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS,
                },
            ],
        });
        }

        // Output the VPC ID
        new cdk.CfnOutput(this, 'VpcId', {
            value: this.vpc.vpcId,
        });

        // Output the Subnet IDs
        this.vpc.publicSubnets.forEach((subnet, index) => {
            new cdk.CfnOutput(this, `PublicSubnet${index}Id`, {
                value: subnet.subnetId,
            });
        });

        this.vpc.privateSubnets.forEach((subnet, index) => {
            new cdk.CfnOutput(this, `PrivateSubnet${index}Id`, {
                value: subnet.subnetId,
            });
        });
    }
}