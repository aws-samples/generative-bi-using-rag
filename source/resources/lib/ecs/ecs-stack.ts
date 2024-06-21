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
  public readonly streamlitEndpoint: string;
  public readonly frontendEndpoint: string;
  public readonly apiEndpoint: string;
constructor(scope: Construct, id: string, props: cdk.StackProps & { aosEndpoint: string }) {
    super(scope, id, props);
    // Create a VPC
    this._vpc = ec2.Vpc.fromLookup(this, "VPC", {
        isDefault: true,
    });
      

    // Get the AOS password secret
    const aosPasswordSecret = secretsmanager.Secret.fromSecretNameV2(this, 'AOSPasswordSecret', 'aosPasswordSecret');

    // Create ECR repositories and Docker image assets
    const services = [
      { name: 'genbi-streamlit', dockerfile: 'Dockerfile', port: 8501, dockerfileDirectory: path.join(__dirname, '../../../../application')},
      { name: 'genbi-frontend', dockerfile: 'Dockerfile', port: 3000, dockerfileDirectory: path.join(__dirname, '../../../../report-front-end')},
      { name: 'genbi-api', dockerfile: 'Dockerfile-api', port: 8000, dockerfileDirectory: path.join(__dirname, '../../../../application')},
    ];

    const repositoriesAndImages = services.map(service => {
      const repository = new ecr.Repository(this, `${service.name}Repository`, {
        repositoryName: `${service.name.toLowerCase()}-repository`,
        removalPolicy: cdk.RemovalPolicy.DESTROY,  // only for demo purposes
      });

      const dockerImageAsset = new DockerImageAsset(this, `${service.name}DockerImage`, {
        directory: service.dockerfileDirectory, // Dockerfile location
        file: service.dockerfile, // Dockerfile filename
      });

      return { repository, dockerImageAsset, port: service.port };
    });

    //  Create an ECS cluster
    const cluster = new ecs.Cluster(this, 'GenBiCluster', {
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
    // ======= 1. Streamlit Service =======
    const taskDefinitionStreamlit = new ecs.FargateTaskDefinition(this, 'GenBiTaskDefinitionStreamlit', {
      memoryLimitMiB: 512,
      cpu: 256,
      executionRole: taskExecutionRole,
      taskRole: taskRole
    });

    const containerStreamlit = taskDefinitionStreamlit.addContainer('GenBiContainerStreamlit', {
      image: ecs.ContainerImage.fromDockerImageAsset(repositoriesAndImages[0].dockerImageAsset),
      memoryLimitMiB: 512,
      cpu: 256,
      logging: new ecs.AwsLogDriver({
        streamPrefix: 'GenBiStreamlit',
      }),
    });

    // add environment variables
    containerStreamlit.addEnvironment('AOS_HOST', props.aosEndpoint);
    containerStreamlit.addEnvironment('AOS_PORT', '443');
    containerStreamlit.addEnvironment('AOS_USER', 'master-user');
    containerStreamlit.addEnvironment('AOS_PASSWORD', aosPasswordSecret.toString());
    containerStreamlit.addPortMappings({
      containerPort: repositoriesAndImages[0].port,
    });

    const fargateServiceStreamlit = new ecs_patterns.ApplicationLoadBalancedFargateService(this, 'GenBiFargateServiceStreamlit', {
      cluster: cluster,
      taskDefinition: taskDefinitionStreamlit,
      publicLoadBalancer: true,
      taskSubnets: { subnetType: ec2.SubnetType.PUBLIC },
      assignPublicIp: true
    });

    // ======= 2. Frontend Service =======
    const taskDefinitionFrontend = new ecs.FargateTaskDefinition(this, 'GenBiTaskDefinitionFrontend', {
      memoryLimitMiB: 512,
      cpu: 256,
      executionRole: taskExecutionRole,
      taskRole: taskRole
    });

    const containerFrontend = taskDefinitionFrontend.addContainer('GenBiContainerFrontend', {
      image: ecs.ContainerImage.fromDockerImageAsset(repositoriesAndImages[1].dockerImageAsset),
      memoryLimitMiB: 512,
      cpu: 256,
      logging: new ecs.AwsLogDriver({
        streamPrefix: 'GenBiFrontend',
      }),
    });

    containerFrontend.addPortMappings({
      containerPort: repositoriesAndImages[1].port,
    });

    const fargateServiceFrontend = new ecs_patterns.ApplicationLoadBalancedFargateService(this, 'GenBiFargateServiceFrontend', {
      cluster: cluster,
      taskDefinition: taskDefinitionFrontend,
      publicLoadBalancer: true,
      taskSubnets: { subnetType: ec2.SubnetType.PUBLIC },
      assignPublicIp: true
    });

    // ======= 3. API Service =======
    const taskDefinitionAPI = new ecs.FargateTaskDefinition(this, 'GenBiTaskDefinitionAPI', {
      memoryLimitMiB: 512,
      cpu: 256,
      executionRole: taskExecutionRole,
      taskRole: taskRole
    });

    const containerAPI = taskDefinitionAPI.addContainer('GenBiContainerAPI', {
      image: ecs.ContainerImage.fromDockerImageAsset(repositoriesAndImages[2].dockerImageAsset),
      memoryLimitMiB: 512,
      cpu: 256,
      logging: new ecs.AwsLogDriver({
        streamPrefix: 'GenBiAPI',
      }),
    });

    // add environment variables
    containerAPI.addEnvironment('AOS_HOST', props.aosEndpoint);
    containerAPI.addEnvironment('AOS_PORT', '443');
    containerAPI.addEnvironment('AOS_USER', 'master-user');
    containerAPI.addEnvironment('AOS_PASSWORD', aosPasswordSecret.toString());
    containerAPI.addPortMappings({
      containerPort: repositoriesAndImages[2].port,
    });

    const fargateServiceAPI = new ecs_patterns.ApplicationLoadBalancedFargateService(this, 'GenBiFargateServiceAPI', {
      cluster: cluster,
      taskDefinition: taskDefinitionAPI,
      publicLoadBalancer: true,
      taskSubnets: { subnetType: ec2.SubnetType.PUBLIC },
      assignPublicIp: true
    });

    // Output the endpoint
    this.streamlitEndpoint = fargateServiceStreamlit.loadBalancer.loadBalancerDnsName;
    this.frontendEndpoint = fargateServiceFrontend.loadBalancer.loadBalancerDnsName;
    this.apiEndpoint = fargateServiceAPI.loadBalancer.loadBalancerDnsName;

    new cdk.CfnOutput(this, 'StreamlitEndpoint', {
      value: this.streamlitEndpoint,
      description: 'The endpoint of the Streamlit service'
    });

    new cdk.CfnOutput(this, 'FrontendEndpoint', {
      value: this.frontendEndpoint,
      description: 'The endpoint of the Frontend service'
    });

    new cdk.CfnOutput(this, 'APIEndpoint', {
      value: this.apiEndpoint,
      description: 'The endpoint of the API service'
    });
  }
}