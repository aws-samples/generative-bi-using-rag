import * as cdk from 'aws-cdk-lib';
import { MainStack } from '../lib/main-stack';
import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';

const devEnv = {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION,
};

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const configPath = path.join(__dirname, '..', 'cdk-config.json');
const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));

const app = new cdk.App();

const rds = config.rds

const cdkConfig = {
    env: devEnv,
    deployRds: rds.deploy
};

new MainStack(app, 'GenBiMainStack', cdkConfig); // Pass deployRDS flag to MainStack constructor
app.synth();
