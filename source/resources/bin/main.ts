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
    bedrock_embedding_name: embedding.bedrock_embedding_name,
    embedding_dimension: embedding.embedding_dimension,
    opensearch_sql_index : opensearch.sql_index,
    opensearch_ner_index : opensearch.ner_index,
    opensearch_cot_index : opensearch.cot_index,
    vpc_id : vpc.id
};

new MainStack(app, 'GenBiMainStack', cdkConfig); // Pass deployRDS flag to MainStack constructor
app.synth();
