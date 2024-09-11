import * as cdk from 'aws-cdk-lib';
import { MainStack } from '../lib/main-stack';
import * as fs from 'fs';
import * as path from 'path';

const devEnv = {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION,
};

declare const __dirname: string;

const configPath = path.join(__dirname, '..', 'cdk-config.json');
const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));

const app = new cdk.App();

const rds = config.rds

const embedding = config.embedding

const opensearch = config.opensearch

const vpc = config.vpc

const cdkConfig = {
    env: devEnv,
    deployRds: rds.deploy,
    embedding_platform: embedding.embedding_platform,
    embedding_region: embedding.embedding_region,
    embedding_name: embedding.embedding_name,
    embedding_dimension: embedding.embedding_dimension,
    sql_index : opensearch.sql_index,
    ner_index : opensearch.ner_index,
    cot_index : opensearch.cot_index,
    log_index : opensearch.log_index,
    existing_vpc_id : vpc.existing_vpc_id,
    bedrock_ak_sk : config.ecs.bedrock_ak_sk,
    bedrock_region: config.ecs.bedrock_region,
    cognito_sign_in_aliases_username: config.cognito.sign_in_aliases_username
};

new MainStack(app, 'GenBiMainStack', cdkConfig); // Pass deployRDS flag to MainStack constructor
app.synth();
