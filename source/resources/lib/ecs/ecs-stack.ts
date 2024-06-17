import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as ecr from 'aws-cdk-lib/aws-ecr';
import * as iam from 'aws-cdk-lib/aws-iam';
import { DockerImageAsset } from 'aws-cdk-lib/aws-ecr-assets';
import * as ecs_patterns from 'aws-cdk-lib/aws-ecs-patterns';
import * as path from 'path';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';

export class ECSStack extends cdk.Stack {
  _vpc;
  public readonly endpoint: string;
constructor(scope: Construct, id: string, props: cdk.StackProps & { aosEndpoint: string }) {
    super(scope, id, props);
    // Create a VPC
    this._vpc = ec2.Vpc.fromLookup(this, "VPC", {
        isDefault: true,
    });
      
    // Dockerfile location
    const dockerfileDirectory = path.join(__dirname, '../../../../application');

    // Get the AOS password secret
    const aosPasswordSecret = secretsmanager.Secret.fromSecretNameV2(this, 'AOSPasswordSecret', 'aosPasswordSecret');

    // Create ECR repositories and Docker image assets
    const services = [
      { name: 'genbi-streamlit', dockerfile: 'Dockerfile', port: 8501},
      // { name: 'genbi-frontend', dockerfile: 'Dockerfile-b', port: 3000},
      // { name: 'genbi-api', dockerfile: 'Dockerfile-api', port: 8000 },
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
      vpc: this._vpc,
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
      const taskDefinition = new ecs.FargateTaskDefinition(this, `GenBiTaskDefinition${index + 1}`, {
        memoryLimitMiB: 512,
        cpu: 256,
        executionRole: taskExecutionRole,
        taskRole: taskRole
      });

      const container = taskDefinition.addContainer(`GenBiContainer${index + 1}`, {
        image: ecs.ContainerImage.fromDockerImageAsset(dockerImageAsset),
        memoryLimitMiB: 512,
        cpu: 256,
      });

      // add environment variables
      container.addEnvironment('AOS_HOST', props.aosEndpoint);
      container.addEnvironment('AOS_PORT', '443');
      container.addEnvironment('AOS_USER', 'master-user');
      container.addEnvironment('AOS_PASSWORD', aosPasswordSecret.toString());
      container.addPortMappings({
        containerPort: port,
      });

      const fargateService = new ecs_patterns.ApplicationLoadBalancedFargateService(this, `GenBiFargateService${index + 1}`, {
        cluster: cluster,
        taskDefinition: taskDefinition,
        publicLoadBalancer: true,
        taskSubnets: { subnetType: ec2.SubnetType.PUBLIC },
        assignPublicIp: true
      });
    });
  }
}