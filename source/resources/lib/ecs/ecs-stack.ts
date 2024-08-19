import * as cdk from 'aws-cdk-lib';
import {Construct} from 'constructs';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as ecr from 'aws-cdk-lib/aws-ecr';
import * as iam from 'aws-cdk-lib/aws-iam';
import {DockerImageAsset, Platform} from 'aws-cdk-lib/aws-ecr-assets';
import * as ecs_patterns from 'aws-cdk-lib/aws-ecs-patterns';
import * as path from 'path';

interface ECSStackProps extends cdk.StackProps {
  vpc: ec2.Vpc;
  subnets: ec2.ISubnet[];
  cognitoUserPoolId: string;
  authenticationType: string;
  cognitoUserPoolClientId: string;
  OSMasterUserSecretName: string;
  OSHostSecretName: string;
}

export class ECSStack extends cdk.Stack {
    public readonly streamlitEndpoint: string;
    public readonly frontendEndpoint: string;
    public readonly apiEndpoint: string;
    public readonly ecsSecurityGroup: ec2.SecurityGroup;

    constructor(scope: Construct, id: string, props: ECSStackProps) {
        super(scope, id, props);

        // const isolatedSubnets = this._vpc.selectSubnets({ subnetType: ec2.SubnetType.PRIVATE_ISOLATED }).subnets;
        // const privateSubnets = this._vpc.selectSubnets({ subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS }).subnets;

        // const nonPublicSubnets = [...isolatedSubnets, ...privateSubnets];
        // const subnets = this._vpc.selectSubnets().subnets;

        // Create ECR repositories and Docker image assets
        const services = [
            {
                name: 'genbi-streamlit',
                dockerfile: 'Dockerfile',
                port: 8501,
                dockerfileDirectory: path.join(__dirname, '../../../../application')
            },
            {
                name: 'genbi-api',
                dockerfile: 'Dockerfile-api',
                port: 8000,
                dockerfileDirectory: path.join(__dirname, '../../../../application')
            },
            {
                name: 'genbi-frontend',
                dockerfile: 'Dockerfile',
                port: 80,
                dockerfileDirectory: path.join(__dirname, '../../../../report-front-end')
            },
        ];

        const awsRegion = props.env?.region as string;

        const GenBiStreamlitDockerImageAsset = {
            'dockerImageAsset': new DockerImageAsset(this, 'GenBiStreamlitDockerImage', {
                directory: services[0].dockerfileDirectory,
                file: services[0].dockerfile,
                platform: Platform.LINUX_AMD64,
                buildArgs: {
                    AWS_REGION: awsRegion, // Pass the AWS region as a build argument
                },
            }), 'port': services[0].port
        };

        const GenBiAPIDockerImageAsset = {
            'dockerImageAsset': new DockerImageAsset(this, 'GenBiAPIDockerImage', {
                directory: services[1].dockerfileDirectory,
                file: services[1].dockerfile,
                platform: Platform.LINUX_AMD64,
                buildArgs: {
                    AWS_REGION: awsRegion, // Pass the AWS region as a build argument
                }
            }), 'port': services[1].port
        };

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
                "secretsmanager:GetSecretValue",
                "secretsmanager:CreateSecret",
            ],
            resources: [
                `arn:${this.partition}:secretsmanager:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:secret:opensearch-host-url*`,
                `arn:${this.partition}:secretsmanager:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:secret:opensearch-master-user*`,
                `arn:${this.partition}:secretsmanager:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:secret:GenBI-*`
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

        // Add SageMaker endpoint access policy
        const sageMakerEndpointAccessPolicy = new iam.PolicyStatement({
            actions: [
                "sagemaker:InvokeEndpoint",
                "sagemaker:DescribeEndpoint",
                "sagemaker:ListEndpoints"
            ],
            resources: [
                `arn:${this.partition}:sagemaker:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:endpoint/*`
            ]
        });
        taskRole.addToPolicy(sageMakerEndpointAccessPolicy);


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
        // containerStreamlit.addEnvironment('SAGEMAKER_EMBEDDING_REGION', cdk.Aws.REGION);
        // containerStreamlit.addEnvironment('SAGEMAKER_SQL_REGION', cdk.Aws.REGION);
        // containerStreamlit.addEnvironment('SAGEMAKER_ENDPOINT_EMBEDDING', '');
        // containerStreamlit.addEnvironment('SAGEMAKER_ENDPOINT_SQL', '');
        containerStreamlit.addEnvironment('BEDROCK_REGION', cdk.Aws.REGION);
        containerStreamlit.addEnvironment('RDS_REGION_NAME', cdk.Aws.REGION);
        containerStreamlit.addEnvironment('AWS_DEFAULT_REGION', cdk.Aws.REGION);
        containerStreamlit.addEnvironment('DYNAMODB_AWS_REGION', cdk.Aws.REGION);
        containerStreamlit.addEnvironment('OPENSEARCH_SECRETS_URL_HOST', props.OSHostSecretName)
        containerStreamlit.addEnvironment('OPENSEARCH_SECRETS_USERNAME_PASSWORD', props.OSMasterUserSecretName)
        containerStreamlit.addPortMappings({
            containerPort: GenBiStreamlitDockerImageAsset.port,
        });

        this.ecsSecurityGroup = new ec2.SecurityGroup(this, 'GenBIECSSecurityGroup', {
            vpc: props.vpc,
            allowAllOutbound: true,
            description: 'Security group for ECS tasks',
        });

        const fargateServiceStreamlit = new ecs_patterns.ApplicationLoadBalancedFargateService(this, 'GenBiFargateServiceStreamlit', {
            cluster: cluster,
            taskDefinition: taskDefinitionStreamlit,
            publicLoadBalancer: true,
            taskSubnets: {subnets: props.subnets},
            assignPublicIp: true,
            securityGroups: [this.ecsSecurityGroup],
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
        // containerAPI.addEnvironment('SAGEMAKER_EMBEDDING_REGION', cdk.Aws.REGION);
        // containerAPI.addEnvironment('SAGEMAKER_SQL_REGION', cdk.Aws.REGION);
        // containerAPI.addEnvironment('SAGEMAKER_ENDPOINT_EMBEDDING', '');
        // containerAPI.addEnvironment('SAGEMAKER_ENDPOINT_SQL', '');
        containerAPI.addEnvironment('VITE_LOGIN_TYPE', props.authenticationType)
        containerAPI.addEnvironment('VITE_COGNITO_REGION', cdk.Aws.REGION)
        containerAPI.addEnvironment('VITE_COGNITO_USER_POOL_ID', props.cognitoUserPoolId)
        containerAPI.addEnvironment('VITE_COGNITO_USER_POOL_WEB_CLIENT_ID', props.cognitoUserPoolClientId)
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
            taskSubnets: {subnets: props.subnets},
            assignPublicIp: true,
            securityGroups: [this.ecsSecurityGroup],
        });

        // ======= 3. Frontend Service =======
        const GenBiFrontendDockerImageAsset = {
            'dockerImageAsset': new DockerImageAsset(this, 'GenBiFrontendDockerImage', {
                directory: services[2].dockerfileDirectory,
                file: services[2].dockerfile,
                platform: Platform.LINUX_AMD64,
                buildArgs: {
                    AWS_REGION: awsRegion, // Pass the AWS region as a build argument
                }
            }), 'port': services[2].port
        };

        const taskDefinitionFrontend = new ecs.FargateTaskDefinition(this, 'GenBiTaskDefinitionFrontend', {
            memoryLimitMiB: 512,
            cpu: 256,
            executionRole: taskExecutionRole,
            taskRole: taskRole
        });

        const containerFrontend = taskDefinitionFrontend.addContainer('GenBiContainerFrontend', {
            image: ecs.ContainerImage.fromDockerImageAsset(GenBiFrontendDockerImageAsset.dockerImageAsset),
            memoryLimitMiB: 512,
            cpu: 256,
            logging: new ecs.AwsLogDriver({
                streamPrefix: 'GenBiFrontend',
            }),
        });

        containerFrontend.addEnvironment('VITE_TITLE', 'Guidance for Generative BI')
        containerFrontend.addEnvironment('VITE_LOGO', '/logo.png');
        containerFrontend.addEnvironment('VITE_RIGHT_LOGO', '');
        containerFrontend.addEnvironment('VITE_LOGIN_TYPE', props.authenticationType);
        containerFrontend.addEnvironment('VITE_COGNITO_REGION', cdk.Aws.REGION);
        containerFrontend.addEnvironment('VITE_COGNITO_USER_POOL_ID', props.cognitoUserPoolId);
        containerFrontend.addEnvironment('VITE_COGNITO_USER_POOL_WEB_CLIENT_ID', props.cognitoUserPoolClientId);
        containerFrontend.addEnvironment('VITE_COGNITO_IDENTITY_POOL_ID', '');
        containerFrontend.addEnvironment('VITE_SQL_DISPLAY', 'yes');
        containerFrontend.addEnvironment('VITE_BACKEND_URL', `http://${fargateServiceAPI.loadBalancer.loadBalancerDnsName}/`);
        containerFrontend.addEnvironment('VITE_WEBSOCKET_URL', `ws://${fargateServiceAPI.loadBalancer.loadBalancerDnsName}/qa/ws`);
        containerFrontend.addEnvironment('VITE_LOGIN_TYPE', 'Cognito');

        containerFrontend.addPortMappings({
            containerPort: GenBiFrontendDockerImageAsset.port,
        });

        const fargateServiceFrontend = new ecs_patterns.ApplicationLoadBalancedFargateService(this, 'GenBiFargateServiceFrontend', {
            cluster: cluster,
            taskDefinition: taskDefinitionFrontend,
            publicLoadBalancer: true,
            // taskSubnets: { subnetType: ec2.SubnetType.PUBLIC },
            taskSubnets: {subnets: props.subnets},
            assignPublicIp: true,
            securityGroups: [this.ecsSecurityGroup],
        });

        this.streamlitEndpoint = fargateServiceStreamlit.loadBalancer.loadBalancerDnsName;
        this.apiEndpoint = fargateServiceAPI.loadBalancer.loadBalancerDnsName;
        this.frontendEndpoint = fargateServiceFrontend.loadBalancer.loadBalancerDnsName;

        new cdk.CfnOutput(this, 'StreamlitEndpoint', {
            value: fargateServiceStreamlit.loadBalancer.loadBalancerDnsName,
            description: 'The endpoint of the Streamlit service'
        });

        new cdk.CfnOutput(this, 'APIEndpoint', {
            value: fargateServiceAPI.loadBalancer.loadBalancerDnsName,
            description: 'The endpoint of the API service'
        });

        new cdk.CfnOutput(this, 'FrontendEndpoint', {
            value: fargateServiceFrontend.loadBalancer.loadBalancerDnsName,
            description: 'The endpoint of the Frontend service'
        });
    }
}