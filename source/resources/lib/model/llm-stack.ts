
import * as cdk from "aws-cdk-lib";
import * as iam from "aws-cdk-lib/aws-iam";
import * as sagemaker from "aws-cdk-lib/aws-sagemaker";
import { Construct } from "constructs";


interface LLMStackProps extends cdk.StackProps {
  s3ModelAssets: string;
  embeddingModelPrefix: string;
  embeddingModelVersion: string;
  sqlModelPrefix: string;
  sqlModelVersion: string;
  llmModelPrefix: string;
  llmModelVersion: string;
  env: cdk.Environment;
}

export class LLMStack extends cdk.NestedStack {
  public stackEmbeddingEndpointName: string = "";
  public stackSqlEndpointName: string = "";
  public stackLlmEndpointName: string = "";

  constructor(scope: Construct, id: string, props: LLMStackProps) {
    super(scope, id, props);

    const llmImageUrlDomain =
      props.env.region === "cn-north-1" || props.env.region === "cn-northwest-1"
        ? ".amazonaws.com.cn/"
        : ".amazonaws.com/";

    const llmImageUrlAccount =
      props.env.region === "cn-north-1" || props.env.region === "cn-northwest-1"
        ? "727897471807.dkr.ecr."
        : "763104351884.dkr.ecr.";

    // Create IAM execution role
    const executionRole = new iam.Role(this, "genbi-endpoint-execution-role", {
      assumedBy: new iam.ServicePrincipal("sagemaker.amazonaws.com"),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName("AmazonSageMakerFullAccess"),
        iam.ManagedPolicy.fromAwsManagedPolicyName("AmazonS3FullAccess"),
        iam.ManagedPolicy.fromAwsManagedPolicyName("CloudWatchLogsFullAccess"),
      ],
    });

    // EMBEDDING MODEL
    const embeddingModelPrefix = props.embeddingModelPrefix;
    const embeddingCodePrefix = embeddingModelPrefix + "_deploy_code";
    const embeddingVersionId = props.embeddingModelVersion;
    const embeddingModelName = "embedding-model-" + embeddingVersionId.slice(0, 5);
    const embeddingConfigName =
      "embedding-endpoint-config-" + embeddingVersionId.slice(0, 5);
    const embeddingEndpointName =
      "embedding-" + embeddingModelPrefix + "-" + embeddingVersionId.slice(0, 5);
    const embeddingImageUrl =
      llmImageUrlAccount +
      props.env.region +
      llmImageUrlDomain +
      "djl-inference:0.26.0-deepspeed0.12.6-cu121";
    const embeddingModel = new sagemaker.CfnModel(this, embeddingModelName, {
      executionRoleArn: executionRole.roleArn,
      primaryContainer: {
        image: embeddingImageUrl,
        modelDataUrl: `s3://${props.s3ModelAssets}/${embeddingCodePrefix}/model.tar.gz`,
        environment: {
          S3_CODE_PREFIX: embeddingCodePrefix,
        },
      }
    })

    // Create endpoint configuration, refer to https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_sagemaker.CfnEndpointConfig.html for full options
    const embeddingEndpointConfig = new sagemaker.CfnEndpointConfig(
      this,
      embeddingConfigName,
      {
        productionVariants: [
          {
            initialVariantWeight: 1.0,
            modelName: embeddingModel.attrModelName,
            variantName: "variantProd",
            containerStartupHealthCheckTimeoutInSeconds: 15 * 60,
            initialInstanceCount: 1,
            instanceType: "ml.g4dn.2xlarge",
          },
        ],
      },
    );

    // Create endpoint
    const embeddingTag: cdk.CfnTag = {
      key: "version",
      value: embeddingVersionId,
    };

    const embeddingTagArray = [embeddingTag];

    const embeddingEndpoint = new sagemaker.CfnEndpoint(
      this,
      embeddingEndpointName,
      {
        endpointConfigName: embeddingEndpointConfig.attrEndpointConfigName,
        endpointName: embeddingEndpointName,
        tags: embeddingTagArray,
      },
    );

    // SQL Model
    const sqlModelPrefix = props.sqlModelPrefix;
    const sqlCodePrefix = sqlModelPrefix + "_deploy_code";
    const sqlVersionId = props.sqlModelVersion;
    const sqlModelName = "sql-model-" + sqlVersionId.slice(0, 5);
    const sqlConfigName =
      "sql-endpoint-config-" + sqlVersionId.slice(0, 5);
    const sqlEndpointName =
      "sql-" + sqlModelPrefix + "-" + sqlVersionId.slice(0, 5);

    const sqlImageUrl =
      llmImageUrlAccount +
      props.env.region +
      llmImageUrlDomain +
      "djl-inference:0.26.0-deepspeed0.12.6-cu121";
    const sqlModel = new sagemaker.CfnModel(this, sqlModelName, {
      executionRoleArn: executionRole.roleArn,
      primaryContainer: {
        image: sqlImageUrl,
        modelDataUrl: `s3://${props.s3ModelAssets}/${sqlCodePrefix}/model.tar.gz`,
        environment: {
          S3_CODE_PREFIX: sqlCodePrefix,
        },
      }
    })

    const sqlEndpointConfig = new sagemaker.CfnEndpointConfig(
      this,
      sqlConfigName,
      {
        productionVariants: [
          {
            initialVariantWeight: 1.0,
            modelName: sqlModel.attrModelName,
            variantName: "variantProd",
            containerStartupHealthCheckTimeoutInSeconds: 15 * 60,
            initialInstanceCount: 1,
            instanceType: "ml.g4dn.2xlarge",
          },
        ],
      },
    );

    const sqlTag: cdk.CfnTag = {
      key: "version",
      value: sqlVersionId,
    };

    const sqlTagArray = [sqlTag];

    const sqlEndpoint = new sagemaker.CfnEndpoint(
      this,
      sqlEndpointName,
      {
        endpointConfigName: sqlEndpointConfig.attrEndpointConfigName,
        endpointName: sqlEndpointName,
        tags: sqlTagArray,
      },
    );


    // INSTRUCT MODEL
    // Create model, BucketDeployment construct automatically handles dependencies to ensure model assets uploaded before creating the model in props.env.region
    // Instruct MODEL
    const llmModelPrefix = props.llmModelPrefix;
    const llmCodePrefix = llmModelPrefix + "_deploy_code";
    const llmVersionId = props.llmModelVersion;
    const llmModelName = "llm-model-" + embeddingVersionId.slice(0, 5);
    const llmConfigName =
      "llm-endpoint-config-" + embeddingVersionId.slice(0, 5);
    const llmEndpointName =
      "llm-" + llmModelPrefix + "-" + embeddingVersionId.slice(0, 5);

    const llmImageUrl =
      llmImageUrlAccount +
      props.env.region +
      llmImageUrlDomain +
      "djl-inference:0.26.0-deepspeed0.12.6-cu121";
    const llmModel = new sagemaker.CfnModel(this, llmModelName, {
      executionRoleArn: executionRole.roleArn,
      primaryContainer: {
        image: llmImageUrl,
        modelDataUrl: `s3://${props.s3ModelAssets}/${llmCodePrefix}/model.tar.gz`,
        environment: {
          S3_CODE_PREFIX: llmCodePrefix,
        },
      },
    });

    // Create endpoint configuration, refer to https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_sagemaker.CfnEndpointConfig.html for full options
    const llmEndpointConfig = new sagemaker.CfnEndpointConfig(
      this,
      llmConfigName,
      {
        productionVariants: [
          {
            initialVariantWeight: 1.0,
            modelName: llmModel.attrModelName,
            variantName: "variantProd",
            containerStartupHealthCheckTimeoutInSeconds: 15 * 60,
            initialInstanceCount: 1,
            instanceType: "ml.g4dn.4xlarge",
          },
        ],
      },
    );

    const llmTag: cdk.CfnTag = {
      key: "version",
      value: llmVersionId,
    };

    const llmTagArray = [llmTag];

    // Create endpoint
    const llmEndpoint = new sagemaker.CfnEndpoint(
      this,
      llmEndpointName,
      {
        endpointConfigName: llmEndpointConfig.attrEndpointConfigName,
        endpointName: llmEndpointName,
        tags: llmTagArray,
      },
    );

    this.stackEmbeddingEndpointName = embeddingEndpointName;
    this.stackSqlEndpointName = sqlEndpointName;
    this.stackLlmEndpointName = llmEndpointName;

  }
}
