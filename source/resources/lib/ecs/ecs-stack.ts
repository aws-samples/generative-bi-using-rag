import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as ecr from 'aws-cdk-lib/aws-ecr';
import * as iam from 'aws-cdk-lib/aws-iam';
import { DockerImageAsset } from 'aws-cdk-lib/aws-ecr-assets';
import * as ecs_patterns from 'aws-cdk-lib/aws-ecs-patterns';
import * as path from 'path';

export class ECSStack extends cdk.Stack {
  public readonly streamlitEndpoint: string;
  public readonly frontendEndpoint: string;
  public readonly apiEndpoint: string;
constructor(scope: Construct, id: string, props: cdk.StackProps 
  & { vpc: ec2.Vpc}
  & { subnets: cdk.aws_ec2.ISubnet[] } & { cognitoUserPoolId: string} 
  & { cognitoUserPoolClientId: string} & {OSMasterUserSecretName: string} 
  & {OSHostSecretName: string}) {
    super(scope, id, props);

    // 选择所有的 isolated 和 private with egress 子网
    // const isolatedSubnets = this._vpc.selectSubnets({ subnetType: ec2.SubnetType.PRIVATE_ISOLATED }).subnets;
    // const privateSubnets = this._vpc.selectSubnets({ subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS }).subnets;

    // 合并所有非公共子网
    // const nonPublicSubnets = [...isolatedSubnets, ...privateSubnets];
    // const subnets = this._vpc.selectSubnets().subnets;

    // Create ECR repositories and Docker image assets
    const services = [
      { name: 'genbi-streamlit', dockerfile: 'Dockerfile', port: 8501, dockerfileDirectory: path.join(__dirname, '../../../../application')},
      { name: 'genbi-api', dockerfile: 'Dockerfile-api', port: 8000, dockerfileDirectory: path.join(__dirname, '../../../../application')},
      // { name: 'genbi-frontend', dockerfile: 'Dockerfile', port: 80, dockerfileDirectory: path.join(__dirname, '../../../../report-front-end')},
    ];

    // const repositoriesAndImages = services.map(service => {
    //   const dockerImageAsset = new DockerImageAsset(this, `${service.name}DockerImage`, {
    //     directory: service.dockerfileDirectory, // Dockerfile location
    //     file: service.dockerfile, // Dockerfile filename
    //   });
    //   return { dockerImageAsset, port: service.port };
    // });

    const GenBiStreamlitDockerImageAsset = {'dockerImageAsset': new DockerImageAsset(this, 'GenBiStreamlitDockerImage', {
        directory: services[0].dockerfileDirectory, 
        file: services[0].dockerfile, 
      }), 'port': services[0].port};
          
    const GenBiAPIDockerImageAsset = {'dockerImageAsset': new DockerImageAsset(this, 'GenBiAPIDockerImage', {
      directory: services[1].dockerfileDirectory, 
      file: services[1].dockerfile, 
    }), 'port': services[1].port};
    
    //  Create an ECS cluster
    const cluster = new ecs.Cluster(this, 'GenBiCluster', {
      vpc: props.vpc,
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
      `arn:${this.partition}:es:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:domain/*`
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
        `arn:${this.partition}:dynamodb:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:table/*`,
      ]
    });
    taskRole.addToPolicy(dynamoDBAccessPolicy);

    // Add secrets manager access policy
    const opensearchHostUrlSecretAccessPolicy = new iam.PolicyStatement({
      actions: [
      "secretsmanager:GetSecretValue"
      ],
      resources: [
      `arn:${this.partition}:secretsmanager:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:secret:opensearch-host-url*`,
      `arn:${this.partition}:secretsmanager:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:secret:opensearch-master-user*`
      ]
    });
    taskRole.addToPolicy(opensearchHostUrlSecretAccessPolicy);

    // Add Bedrock access policy
    if (props.env?.region !== "cn-north-1" && props.env?.region !== "cn-northwest-1") {
      const bedrockAccessPolicy = new iam.PolicyStatement({
      actions: [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      resources: [
        `arn:${this.partition}:bedrock:${cdk.Aws.REGION}::foundation-model/*`
      ]
      });
      taskRole.addToPolicy(bedrockAccessPolicy);
    } 

    // Add Cognito all access policy
    if (props.env?.region !== "cn-north-1" && props.env?.region !== "cn-northwest-1") {
        const cognitoAccessPolicy = new iam.PolicyStatement({
        actions: [
        "cognito-identity:*",
        "cognito-idp:*"
        ],
        resources: [
        `arn:${this.partition}:cognito-idp:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:userpool/*`,
        `arn:${this.partition}:cognito-identity:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:identitypool/*`
        ]
      });
      taskRole.addToPolicy(cognitoAccessPolicy);
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
      image: ecs.ContainerImage.fromDockerImageAsset(GenBiStreamlitDockerImageAsset.dockerImageAsset),
      memoryLimitMiB: 512,
      cpu: 256,
      logging: new ecs.AwsLogDriver({
        streamPrefix: 'GenBiStreamlit',
      }),
    });

    containerStreamlit.addEnvironment('OPENSEARCH_TYPE', 'service');
    containerStreamlit.addEnvironment('AOS_INDEX', 'uba');
    containerStreamlit.addEnvironment('AOS_INDEX_NER', 'uba_ner');
    containerStreamlit.addEnvironment('AOS_INDEX_AGENT', 'uba_agent');
    containerStreamlit.addEnvironment('EMBEDDING_DIMENSION', '1024');
    containerStreamlit.addEnvironment('SAGEMAKER_ENDPOINT_EMBEDDING', 'mixtral-instruct-awq-g5-2-endpoint');
    containerStreamlit.addEnvironment('SAGEMAKER_ENDPOINT_SQL', 'bge-m3-2024-07-02-03-20-48-638-endpoint');
    containerStreamlit.addEnvironment('BEDROCK_REGION', cdk.Aws.REGION);
    containerStreamlit.addEnvironment('RDS_REGION_NAME', cdk.Aws.REGION);
    containerStreamlit.addEnvironment('AWS_DEFAULT_REGION', cdk.Aws.REGION);
    containerStreamlit.addEnvironment('DYNAMODB_AWS_REGION', cdk.Aws.REGION);
    containerStreamlit.addEnvironment('OPENSEARCH_SECRETS_URL_HOST', props.OSHostSecretName)
    containerStreamlit.addEnvironment('OPENSEARCH_SECRETS_USERNAME_PASSWORD', props.OSMasterUserSecretName)
    containerStreamlit.addPortMappings({
      containerPort: GenBiStreamlitDockerImageAsset.port,
    });

    const fargateServiceStreamlit = new ecs_patterns.ApplicationLoadBalancedFargateService(this, 'GenBiFargateServiceStreamlit', {
      cluster: cluster,
      taskDefinition: taskDefinitionStreamlit,
      publicLoadBalancer: true,
      taskSubnets: { subnets: props.subnets },
      assignPublicIp: false
    });

    // ======= 2. API Service =======
    const taskDefinitionAPI = new ecs.FargateTaskDefinition(this, 'GenBiTaskDefinitionAPI', {
      memoryLimitMiB: 512,
      cpu: 256,
      executionRole: taskExecutionRole,
      taskRole: taskRole
    });

    const containerAPI = taskDefinitionAPI.addContainer('GenBiContainerAPI', {
      image: ecs.ContainerImage.fromDockerImageAsset(GenBiAPIDockerImageAsset.dockerImageAsset),
      memoryLimitMiB: 512,
      cpu: 256,
      logging: new ecs.AwsLogDriver({
        streamPrefix: 'GenBiAPI',
      }),
    });

    containerAPI.addEnvironment('OPENSEARCH_TYPE', 'service');
    containerAPI.addEnvironment('AOS_INDEX', 'uba');
    containerAPI.addEnvironment('AOS_INDEX_NER', 'uba_ner');
    containerAPI.addEnvironment('AOS_INDEX_AGENT', 'uba_agent');
    containerAPI.addEnvironment('EMBEDDING_DIMENSION', '1024');
    containerAPI.addEnvironment('SAGEMAKER_ENDPOINT_EMBEDDING', 'mixtral-instruct-awq-g5-2-endpoint');
    containerAPI.addEnvironment('SAGEMAKER_ENDPOINT_SQL', 'bge-m3-2024-07-02-03-20-48-638-endpoint');
    containerAPI.addEnvironment('BEDROCK_REGION', cdk.Aws.REGION);
    containerAPI.addEnvironment('RDS_REGION_NAME', cdk.Aws.REGION);
    containerAPI.addEnvironment('AWS_DEFAULT_REGION', cdk.Aws.REGION);
    containerAPI.addEnvironment('DYNAMODB_AWS_REGION', cdk.Aws.REGION);
    containerAPI.addEnvironment('OPENSEARCH_SECRETS_URL_HOST', props.OSHostSecretName)
    containerAPI.addEnvironment('OPENSEARCH_SECRETS_USERNAME_PASSWORD', props.OSMasterUserSecretName)

    containerAPI.addPortMappings({
      containerPort: GenBiAPIDockerImageAsset.port,
    });

    const fargateServiceAPI = new ecs_patterns.ApplicationLoadBalancedFargateService(this, 'GenBiFargateServiceAPI', {
      cluster: cluster,
      taskDefinition: taskDefinitionAPI,
      publicLoadBalancer: true,
      taskSubnets: { subnets: props.subnets },
      assignPublicIp: false
    });

    // ======= 3. Frontend Service =======
    // const GenBiFrontendDockerImageAsset = {'dockerImageAsset': new DockerImageAsset(this, 'GenBiFrontendDockerImage', {
    //   directory: services[2].dockerfileDirectory,
    //   file: services[2].dockerfile,
    // }), 'port': services[2].port};
    //
    // const taskDefinitionFrontend = new ecs.FargateTaskDefinition(this, 'GenBiTaskDefinitionFrontend', {
    //   memoryLimitMiB: 512,
    //   cpu: 256,
    //   executionRole: taskExecutionRole,
    //   taskRole: taskRole
    // });
    //
    // const containerFrontend = taskDefinitionFrontend.addContainer('GenBiContainerFrontend', {
    //   image: ecs.ContainerImage.fromDockerImageAsset(GenBiFrontendDockerImageAsset.dockerImageAsset),
    //   memoryLimitMiB: 512,
    //   cpu: 256,
    //   logging: new ecs.AwsLogDriver({
    //     streamPrefix: 'GenBiFrontend',
    //   }),
    // });

    // containerFrontend.addEnvironment('VITE_TITLE', 'Guidance for Generative BI')
    // containerFrontend.addEnvironment('VITE_LOGO', '/logo.png');
    // containerFrontend.addEnvironment('VITE_RIGHT_LOGO', '');
    // containerFrontend.addEnvironment('VITE_COGNITO_REGION', cdk.Aws.REGION);
    // containerFrontend.addEnvironment('VITE_COGNITO_USER_POOL_ID', props.cognitoUserPoolId);
    // containerFrontend.addEnvironment('VITE_COGNITO_USER_POOL_WEB_CLIENT_ID', props.cognitoUserPoolClientId);
    // containerFrontend.addEnvironment('VITE_COGNITO_IDENTITY_POOL_ID', '');
    // containerFrontend.addEnvironment('VITE_SQL_DISPLAY', 'yes');
    // containerFrontend.addEnvironment('VITE_BACKEND_URL', `https://${fargateServiceAPI.loadBalancer.loadBalancerDnsName}/`);
    // containerFrontend.addEnvironment('VITE_WEBSOCKET_URL', `ws://${fargateServiceAPI.loadBalancer.loadBalancerDnsName}/qa/ws`);
    // containerFrontend.addEnvironment('VITE_LOGIN_TYPE', 'Cognito');
    //
    // containerFrontend.addPortMappings({
    //   containerPort: GenBiFrontendDockerImageAsset.port,
    // });
    //
    // const fargateServiceFrontend = new ecs_patterns.ApplicationLoadBalancedFargateService(this, 'GenBiFargateServiceFrontend', {
    //   cluster: cluster,
    //   taskDefinition: taskDefinitionFrontend,
    //   publicLoadBalancer: true,
    //   // taskSubnets: { subnetType: ec2.SubnetType.PUBLIC },
    //   taskSubnets: { subnets: props.subnets },
    //   assignPublicIp: false
    // });

    this.streamlitEndpoint = fargateServiceStreamlit.loadBalancer.loadBalancerDnsName;
    this.apiEndpoint = fargateServiceAPI.loadBalancer.loadBalancerDnsName;
    // this.frontendEndpoint = fargateServiceFrontend.loadBalancer.loadBalancerDnsName;

    new cdk.CfnOutput(this, 'StreamlitEndpoint', {
      value: fargateServiceStreamlit.loadBalancer.loadBalancerDnsName,
      description: 'The endpoint of the Streamlit service'
    });

    new cdk.CfnOutput(this, 'APIEndpoint', {
      value: fargateServiceAPI.loadBalancer.loadBalancerDnsName,
      description: 'The endpoint of the API service'
    });

    // new cdk.CfnOutput(this, 'FrontendEndpoint', {
    //   value: fargateServiceFrontend.loadBalancer.loadBalancerDnsName,
    //   description: 'The endpoint of the Frontend service'
    // });
  }
}