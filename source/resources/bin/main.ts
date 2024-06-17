#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import { MainStack } from '../lib/main-stack';
// import {RDSStack} from '../lib/rds/rds-stack';
// import {AOSStack} from '../lib/aos/aos-stack';
// for development, use account/region from cdk cli
const devEnv = {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION,
};

const app = new cdk.App();
// new AOSStack(app, 'AOSStack', { env: devEnv });
new MainStack(app, 'GenBiMainStack', { env: devEnv });
// new RDSStack(app, 'RDSStack', { env: devEnv })
app.synth();
