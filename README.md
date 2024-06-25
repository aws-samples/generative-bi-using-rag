# Generative BI using RAG on AWS
[中文文档](README_CN.md) | [日本語ドキュメント](README_JP.md)

## Introduction

A NLQ(Natural Language Query) demo using Amazon Bedrock, Amazon OpenSearch with RAG technique.

![Screenshot](./assets/aws-architecture.png)

[User Operation Manual](https://github.com/aws-samples/generative-bi-using-rag/wiki/%E7%94%A8%E6%88%B7%E6%93%8D%E4%BD%9C%E6%89%8B%E5%86%8C)

[Project Data Flowchart](https://github.com/aws-samples/generative-bi-using-rag/wiki/%E9%A1%B9%E7%9B%AE%E6%B5%81%E7%A8%8B%E5%9B%BE)

## Table of Content
1. [Overview](#overview-required)
    - [Cost](#cost)
2. [Prerequisites](#prerequisites-required)
    - [Operating System](#operating-system-required)
3. [Deployment Steps](#deployment-steps-required)
4. [Deployment Validation](#deployment-validation-required)
5. [Running the Guidance](#running-the-guidance-required)
6. [Next Steps](#next-steps-required)
7. [Cleanup](#cleanup-required)
8. [Revisions](#revisions-optional)
9. [Notices](#notices-optional)
10. [Authors](#authors-optional)

## Overview
For Deployment Guide, please refer to [CDK Deployment Guide](source/resources/README.md)

This is a comprehensive framework designed to enable Generative BI capabilities on customized data sources (RDS/Redshift) hosted on AWS. It offers the following key features:
- Text-to-SQL functionality for querying customized data sources using natural language.
- User-friendly interface for adding, editing, and managing data sources, tables, and column descriptions.
- Performance enhancement through the integration of historical question-answer ranking and entity recognition.
- Customize business information, including entity information, formulas, SQL samples, and analysis ideas for complex business problems.
- Add agent task splitting function to handle complex attribution analysis problems.
- Intuitive question-answering UI that provides insights into the underlying Text-to-SQL mechanism.
- Simple agent design interface for handling complex queries through a conversational approach.

### Cost

As of May, 2024, the cost for running this Guidance with the default settings in the _us-west-2_ is approximately $476.74 per month for processing 2000 requests.

### Sample Cost Table

The following table provides a sample cost breakdown for deploying this Guidance with the default parameters in the US East (N. Virginia) Region for one month.

| AWS service  | Dimensions | Cost [USD] per Month |
| ----------- | ------------ | ------------ |
| Amazon ECS | 1 instance t3.large | $ 60.74 |
| Amazon DynamoDB | 25 provisioned write & read capacity units per month | $ 0.00 |
| Amazon Bedrock | 2000 requests per month, with each request consuming 10000 input tokens and 1000 output tokens | $ 416.00 |
| Amazon OpenSearch Service | 1 domain | $ 0.00 |

## Prerequisites

### Operating System
“CDK are optimized to best work to be initiated on **<Amazon Linux 2023 AMI>**.  Deployment in another OS may require additional steps.”

### AWS account requirements

- VPC
- IAM role with specific permissions
- Amazon Bedrock
- Amazon ECS
- Amazon DynamoDB
- Amazon Cognito
- Amazon OpenSearch Service
- Amazon Elastic Load Balancing
- Amazon SageMaker (Optional, if you need customized models to be deployed)
- Amazon Secrets Manager

### Supported Regions

us-west-2, us-east-2, us-east-1, ap-south-1, ap-southeast-1, ap-southeast-2, ap-northeast-1, eu-central-1, eu-west-1, eu-west-3, or any other region that supports the services (bedrock) used in the Guidance.

## Deployment Steps

### 1. Prepare CDK Pre-requisites
Please follow the instructions in the [CDK Workshop](https://cdkworkshop.com/15-prerequisites.html) to install the CDK toolkit. Make sure your environment have the authorization to create the resources.

### 2. Set a password for the Streamlit Web UI

The default password is [Empty] for Streamlit Web UI. If you need to set a password for the Streamlit Web UI, you can update the password in the
```application/config_files/stauth_config.yaml```

for example 

```yaml
credentials:
  usernames:
    jsmith:
      email: jsmith@gmail.com
      name: John Smith
      password: XXXXXX # To be replaced with hashed password
    rbriggs:
      email: rbriggs@gmail.com
      name: Rebecca Briggs
      password: XXXXXX # To be replaced with hashed password
cookie:
  expiry_days: 30
  key: random_signature_key # Must be string
  name: random_cookie_name
preauthorized:
  emails:
  - melsby@gmail.com
```

change the password 'XXXXXX' to hashed password

Use the python code below to generate XXXXXX
```python
from streamlit_authenticator.utilities.hasher import Hasher
hashed_passwords = Hasher(['abc', 'def']).generate()
```

### 3. Deploy the CDK Stack
For global regions, execute the following commands:

Navigate to the CDK project directory:
```
cd generative-bi-using-rag/source/resources
```
Deploy the CDK stack, change the region to your own region if needed, for example, us-west-2, us-east-1, etc.:
```
cdk deploy --context region=us-west-2 --require-approval never
```
You will see the following when deployed succeeded
```
GenBiMainStack.AOSDomainEndpoint = XXXXX.us-west-2.es.amazonaws.com
GenBiMainStack.APIEndpoint = XXXXX.us-west-2.elb.amazonaws.com
GenBiMainStack.FrontendEndpoint = XXXXX.us-west-2.elb.amazonaws.com
GenBiMainStack.StreamlitEndpoint = XXXXX.us-west-2.elb.amazonaws.com
```

## Running the Guidance 

After the CDK stack is deployed, wait around 40 minutes for the initialization to complete. Then, open the Streamlit Web UI in your browser: https://<your-public-dns>

## Cleanup 
- Delete the CDK stack:
```
cdk destroy
```