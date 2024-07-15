import { StackProps, CfnParameter, CfnOutput } from 'aws-cdk-lib';
import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import { AOSStack } from './aos/aos-stack';
// import { LLMStack } from './model/llm-stack';
import { ECSStack } from './ecs/ecs-stack';
import { CognitoStack } from './cognito/cognito-stack';
import { RDSStack } from './rds/rds-stack';
import { VPCStack } from './vpc/vpc-stack';

interface MainStackProps extends StackProps {
  deployRds?: boolean;
}

export class MainStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: MainStackProps={ deployRds: false }) {
    super(scope, id, props);

    const _deployRds = props.deployRds || false;

    // ======== Step 0. Define the VPC =========
    const _VpcStack = new VPCStack(this, 'vpc-Stack', {
      env: props.env,
    });

    // ======== Step 1. Define the LLMStack =========
    // const s3ModelAssetsBucket = new CfnParameter(this, "S3ModelAssetsBucket", {
    //   type: "String",
    //   description: "S3 Bucket for model & code assets",
    //   default: "not-set"
    // });
    
    // ======== Step 2. Define the AOSStack =========
    const selectedSubnets = _VpcStack.vpc.selectSubnets({ subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS });

    const _AosStack = new AOSStack(this, 'aos-Stack', {
      env: props.env,
      vpc: _VpcStack.vpc,
      subnets: selectedSubnets.subnets,
    });

    // 打印选择的私有子网信息
    console.log('Selected PRIVATE_WITH_EGRESS subnets:');
    selectedSubnets.subnets.forEach((subnet, index) => {
      console.log(`Subnet ${index + 1}:`);
      console.log(`  ID: ${subnet.subnetId}`);
      console.log(`  Availability Zone: ${subnet.availabilityZone}`);
      console.log(`  CIDR: ${subnet.ipv4CidrBlock}`);
    });

    // 打印选择的子网数量
    console.log(`Total number of selected subnets: ${selectedSubnets.subnets.length}`);



    const aosEndpoint = _AosStack.endpoint;

    // ======== Step 3. Define the RDSStack =========
    if (_deployRds) {
      const rdsSubnets = _VpcStack.vpc.selectSubnets({ subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS   });

      const _RdsStack = new RDSStack(this, 'rds-Stack', {
        env: props.env,
        subnets: rdsSubnets,
        vpcId : _VpcStack.vpc.vpcId
      });
      new cdk.CfnOutput(this, 'RDSEndpoint', {
        value: _RdsStack.endpoint,
        description: 'The endpoint of the RDS instance',
      });
    }

    // ======== Step 4. Define Cognito =========
    const _CognitoStack = new CognitoStack(this, 'cognito-Stack', {
      env: props.env
    });
    
    // ======== Step 5. Define the ECS ========= 
    // pass the aosEndpoint and aosPassword to the ecs stack
    const _EcsStack = new ECSStack(this, 'ecs-Stack', {
      env: props.env,
      vpc: _VpcStack.vpc,
      subnets: _VpcStack.vpc.selectSubnets({ subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS }).subnets,
      cognitoUserPoolId: _CognitoStack.userPoolId,
      cognitoUserPoolClientId: _CognitoStack.userPoolClientId,
      OSMasterUserSecretName: _AosStack.OSMasterUserSecretName,
      OSHostSecretName: _AosStack.OSHostSecretName,
    });
    _AosStack.addDependency(_VpcStack);
    _EcsStack.addDependency(_AosStack);
    _EcsStack.addDependency(_CognitoStack);
    _EcsStack.addDependency(_VpcStack);

    new cdk.CfnOutput(this, 'AOSDomainEndpoint', {
      value: aosEndpoint,
      description: 'The endpoint of the OpenSearch domain'
    });
    
    new cdk.CfnOutput(this, 'StreamlitEndpoint', {
      value: _EcsStack.streamlitEndpoint,
      description: 'The endpoint of the Streamlit service'
    });
    new cdk.CfnOutput(this, 'FrontendEndpoint', {
      value: _EcsStack.frontendEndpoint,
      description: 'The endpoint of the Frontend service'
    });
    new cdk.CfnOutput(this, 'APIEndpoint', {
      value: _EcsStack.apiEndpoint,
      description: 'The endpoint of the API service'
    });
  }
}