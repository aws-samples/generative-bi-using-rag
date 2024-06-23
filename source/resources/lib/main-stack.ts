import { Duration, Stack, StackProps, CfnParameter, CfnOutput } from 'aws-cdk-lib';
import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import { AOSStack } from './aos/aos-stack';
import { LLMStack } from './model/llm-stack';
import { ECSStack } from './ecs/ecs-stack';
import { CognitoStack } from './cognito/cognito-stack';
import { RDSStack } from './rds/rds-stack';

export class MainStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: StackProps={}) {
    super(scope, id, props);

    // Looking for the default VPC
    const vpc = ec2.Vpc.fromLookup(this, "VPC", {
      isDefault: true,
    });

    // ======== Step 1. Define the LLMStack =========
    const s3ModelAssetsBucket = new CfnParameter(this, "S3ModelAssetsBucket", {
      type: "String",
      description: "S3 Bucket for model & code assets",
      default: "not-set"
    });

    // let _LlmStack;

    // if (props.env?.region === "cn-north-1" || props.env?.region === "cn-northwest-1") {
    //   _LlmStack = new LLMStack(this, 'llm-Stack', {
    //     s3ModelAssets: s3ModelAssetsBucket.valueAsString,
    //     embeddingModelPrefix: 'bge-m3',
    //     embeddingModelVersion: '3ab7155aa9b89ac532b2f2efcc3f136766b91025',
    //     sqlModelPrefix: 'sqlcoder-7b-2',
    //     sqlModelVersion: '7e5b6f7981c0aa7d143f6bec6fa26625bdfcbe66',
    //     llmModelPrefix: 'internlm2-chat-7b',
    //     llmModelVersion: '54a594b0be43065e7b7674d0f236911cd7c465ab',
    //     env: props.env || {},
    //   });
    // }
    
    // ======== Step 2. Define the AOSStack ========= 
    const _AosStack = new AOSStack(this, 'aos-Stack', {
      env: props.env
    });

    const aosEndpoint = _AosStack.endpoint;

    // ======== Step 3. Define the RDSStack =========
    // const _RdsStack = new RDSStack(this, 'rds-Stack', {
    //   env: props.env,
    // });

    // ======== Step 4. Define Cognito =========
    const _CognitoStack = new CognitoStack(this, 'cognito-Stack', {
      env: props.env
    });
    
    // ======== Step 5. Define the ECS ========= 
    // pass the aosEndpoint and aosPassword to the ecs stack
    const _EcsStack = new ECSStack(this, 'ecs-Stack', {
      env: props.env,
      cognitoUserPoolId: _CognitoStack.userPoolId,
      cognitoUserPoolClientId: _CognitoStack.userPoolClientId,
    });

    _EcsStack.addDependency(_AosStack);
    _EcsStack.addDependency(_CognitoStack);

    // if (_LlmStack) {
    //   _EcsStack.addDependency(_LlmStack);
    // }

    new cdk.CfnOutput(this, 'AOSDomainEndpoint', {
      value: aosEndpoint,
      description: 'The endpoint of the OpenSearch domain'
    });
    // new cdk.CfnOutput(this, 'RDSEndpoint', {
    //   value: _RdsStack.endpoint,
    //   description: 'The endpoint of the RDS instance'
    // });
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