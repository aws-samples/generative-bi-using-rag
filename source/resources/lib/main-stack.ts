import { Duration, Stack, StackProps, CfnParameter, CfnOutput } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { Ec2Stack } from './ec2/ec2-stack';
import { LLMStack } from './model/llm-stack';

export class MainStack extends Stack {

  constructor(scope: Construct, id: string, props: StackProps = {}) {
    super(scope, id, props);

    const s3ModelAssetsBucket = new CfnParameter(this, "S3ModelAssetsBucket", {
      type: "String",
      description: "S3 Bucket for model & code assets",
      default: "not-set"
    });

    let _LlmStack;

    if (props.env?.region === "cn-north-1" || props.env?.region === "cn-northwest-1") {
      _LlmStack = new LLMStack(this, 'llm-Stack', {
        s3ModelAssets: s3ModelAssetsBucket.valueAsString,
        embeddingModelPrefix: 'bge-m3',
        embeddingModelVersion: '3ab7155aa9b89ac532b2f2efcc3f136766b91025',
        sqlModelPrefix: 'sqlcoder-7b-2',
        sqlModelVersion: '7e5b6f7981c0aa7d143f6bec6fa26625bdfcbe66',
        llmModelPrefix: 'internlm2-chat-7b',
        llmModelVersion: '54a594b0be43065e7b7674d0f236911cd7c465ab',
        env: props.env || {},
      });
    }

    const _Ec2Stack = new Ec2Stack(this, 'ec2-Stack', {
      env: props.env,
    });

    if (_LlmStack) {
      _Ec2Stack.addDependency(_LlmStack);
    }

    new CfnOutput(this, 'Ec2PublicIP', {
      value: _Ec2Stack._publicIP,
      description: 'Public IP of the EC2 instance',
    });
  }
}
