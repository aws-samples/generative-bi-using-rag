import * as cdk from 'aws-cdk-lib';
import { MainStack } from '../lib/main-stack';

const devEnv = {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION,
};

const app = new cdk.App();
const deployRds = process.argv.includes('--deploy-rds'); // Check if --deploy-rds flag is present

new MainStack(app, 'GenBiMainStack', { env: devEnv, deployRds }); // Pass deployRDS flag to MainStack constructor
app.synth();
