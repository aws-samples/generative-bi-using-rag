import { Duration, Stack, StackProps, CfnParameter, CfnOutput } from 'aws-cdk-lib';
import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import { AOSStack } from './aos/aos-stack';
import { LLMStack } from './model/llm-stack';
import { ECSStack } from './ecs/ecs-stack';
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

    // ======== Step 3. Define the ECS ========= 
    // pass the aosEndpoint and aosPassword to the ecs stack
    const _EcsStack = new ECSStack(this, 'ecs-Stack', {
      env: props.env,
      aosEndpoint: aosEndpoint
    });    

    // ======== Step 4. Define the RDSStack =========
    const _RdsStack = new RDSStack(this, 'rds-Stack', {
      env: props.env,
    });

    // Output the RDS endpoint
    new CfnOutput(this, 'RDSEndpoint', {
      value: _RdsStack.endpoint,
    });

    // ======== Step 5. Add dependencies =========
    _EcsStack.addDependency(_AosStack);

    // if (_LlmStack) {
    //   _EcsStack.addDependency(_LlmStack);
    // }

    new cdk.CfnOutput(this, 'AOSDomainEndpoint', {
      value: aosEndpoint,
      description: 'The endpoint of the OpenSearch domain'
    });

    // ======== Step 6. Run a python script to initiate opensearch =========
    // const ec2Instance = _EcsStack.ec2Instance; // 假设您在 ECSStack 中创建了一个 EC2 实例

    // const userData = ec2.UserData.forLinux();
    // userData.addCommands(
    //     'python3 /path/to/init_rds.py', // 初始化 RDS 脚本
    //     'python3 /path/to/create_opensearch_index.py' // 为 OpenSearch 建立索引脚本
    // );

    // ec2Instance.addUserData(userData);
  }
}