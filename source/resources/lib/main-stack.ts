import { Duration, Stack, StackProps, CfnParameter, CfnOutput } from 'aws-cdk-lib';
import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as ecr from 'aws-cdk-lib/aws-ecr';
import * as ecs_patterns from 'aws-cdk-lib/aws-ecs-patterns';
import * as path from 'path';
import { DockerImageAsset } from 'aws-cdk-lib/aws-ecr-assets';
import { AOSStack } from './aos/aos-stack';
import { LLMStack } from './model/llm-stack';
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
    
    // ======== Step 2. Define the AOSStack ========= 
    // const _AosStack = new AOSStack(this, 'aos-Stack', {
    //   env: props.env,
    // });

    // const aosEndpoint = _AosStack.endpoint;
    
    // if (_LlmStack) {
    //   _Ec2Stack.addDependency(_LlmStack);
    // }

    // ======== Step 3. Define the ECS ========= 

    // Dockerfile location
    const dockerfileDirectory = path.join(__dirname, '../../../application');

    // Create ECR repositories and Docker image assets
    const services = [
      { name: 'nlq-streamlit', dockerfile: 'Dockerfile', port: 8501},
      // { name: 'nlq-frontend', dockerfile: 'Dockerfile-b', port: 3000},
      // { name: 'nlq-api', dockerfile: 'Dockerfile-api', port: 8000 },
    ];

    const repositoriesAndImages = services.map(service => {
      const repository = new ecr.Repository(this, `${service.name}Repository`, {
        repositoryName: `${service.name.toLowerCase()}-repository`,
        removalPolicy: cdk.RemovalPolicy.DESTROY,  // only for demo purposes
      });

      const dockerImageAsset = new DockerImageAsset(this, `${service.name}DockerImage`, {
        directory: dockerfileDirectory, // Dockerfile location
        file: service.dockerfile, // Dockerfile filename
      });

      return { repository, dockerImageAsset, port: service.port };
    });

    //  Create an ECS cluster
    const cluster = new ecs.Cluster(this, 'NLQCluster', {
      vpc: vpc,
    });

    const taskExecutionRole = new iam.Role(this, 'TaskExecutionRole', {
      assumedBy: new iam.ServicePrincipal('ecs-tasks.amazonaws.com'),
    });

    const taskRole = new iam.Role(this, 'TaskRole', {
      assumedBy: new iam.ServicePrincipal('ecs-tasks.amazonaws.com'),
    });

    // Add OpenSearch access policy
    const openSearchAccessPolicy = new iam.PolicyStatement({
      actions: [
      "es:ESHttpGet",
      "es:ESHttpHead",
      "es:ESHttpPut",
      "es:ESHttpPost",
      "es:ESHttpDelete"
      ],
      resources: [
      `arn:aws:es:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:domain/*`
      ]
    });
    taskRole.addToPolicy(openSearchAccessPolicy);

    // Add DynamoDB access policy
    const dynamoDBAccessPolicy = new iam.PolicyStatement({
      actions: [
      "dynamodb:*Table",
      "dynamodb:*Item",
      "dynamodb:Scan",
      "dynamodb:Query"
      ],
      resources: [
        `arn:aws:dynamodb:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:table/*`,
      ]
    });
    taskRole.addToPolicy(dynamoDBAccessPolicy);

    // Add Bedrock access policy
    if (props.env?.region !== "cn-north-1" && props.env?.region !== "cn-northwest-1") {
      const bedrockAccessPolicy = new iam.PolicyStatement({
      actions: [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      resources: [
        `arn:aws:bedrock:${cdk.Aws.REGION}::foundation-model/*`
      ]
      });
      taskRole.addToPolicy(bedrockAccessPolicy);
    } 

    // Create ECS services through Fargate
    repositoriesAndImages.forEach(({ dockerImageAsset, port }, index) => {
      const taskDefinition = new ecs.FargateTaskDefinition(this, `NLQTaskDefinition${index + 1}`, {
        memoryLimitMiB: 512,
        cpu: 256,
        executionRole: taskExecutionRole,
        taskRole: taskRole
      });

      const container = taskDefinition.addContainer(`NLQContainer${index + 1}`, {
        image: ecs.ContainerImage.fromDockerImageAsset(dockerImageAsset),
        memoryLimitMiB: 512,
        cpu: 256,
      });

      // add environment variables
      // container.addEnvironment('AOS_HOST', aosEndpoint);
      container.addEnvironment('AOS_HOST', 'vpc-nlqopensearchdo-4sladpb7aure-oxjyclx5ioidlltnokwragz624.us-west-2.es.amazonaws.com');
      container.addEnvironment('AOS_PORT', '443');
      container.addPortMappings({
        containerPort: port,
      });

      const fargateService = new ecs_patterns.ApplicationLoadBalancedFargateService(this, `MyFargateService${index + 1}`, {
        cluster: cluster,
        taskDefinition: taskDefinition,
        publicLoadBalancer: true,
        taskSubnets: { subnetType: ec2.SubnetType.PUBLIC },
        assignPublicIp: true
      });
    });

    // ======== Step 4. Define the RDSStack =========
    const rdsStack = new RDSStack(this, 'rds-Stack', {
      env: props.env,
    });

    // Output the RDS endpoint
    // new CfnOutput(this, 'RDSEndpoint', {
    //   value: rdsStack.exportValue.databaseInstanceEndpoint,
    // });
  }
}