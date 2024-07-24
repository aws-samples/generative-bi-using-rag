import * as cdk from 'aws-cdk-lib';
import {Construct} from 'constructs';
import * as ec2 from 'aws-cdk-lib/aws-ec2';


export class VPCStack extends cdk.Stack {
    public readonly vpc: ec2.Vpc;
    public readonly publicSubnets: ec2.ISubnet[];

    constructor(scope: Construct, id: string, props: cdk.StackProps) {
        super(scope, id, props);
        // Create a VPC
        const vpc = new ec2.Vpc(this, 'GenBIVpc', {
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

        this.vpc = vpc;

        // Output the VPC ID
        new cdk.CfnOutput(this, 'VpcId', {
            value: vpc.vpcId,
        });

        // Output the Subnet IDs
        vpc.publicSubnets.forEach((subnet, index) => {
            new cdk.CfnOutput(this, `PublicSubnet${index}Id`, {
                value: subnet.subnetId,
            });
        });

        vpc.privateSubnets.forEach((subnet, index) => {
            new cdk.CfnOutput(this, `PrivateSubnet${index}Id`, {
                value: subnet.subnetId,
            });
        });

        // Output NatGatewayId  ID
        new cdk.CfnOutput(this, 'NatGatewayId', {
            value: this.vpc.natGateways[0].gatewayId,
        });

        // Output RouteTable ID
        new cdk.CfnOutput(this, 'PublicRouteTableId', {
            value: this.vpc.publicSubnets[0].routeTable.routeTableId,
        });

        new cdk.CfnOutput(this, 'PrivateRouteTableId', {
            value: this.vpc.privateSubnets[0].routeTable.routeTableId,
        });
    }
}