import * as cdk from 'aws-cdk-lib/core';
import * as cognito from 'aws-cdk-lib/aws-cognito';
import { Construct } from 'constructs';

interface CognitoStackProps extends cdk.StackProps {
    sign_in_aliases_username?: boolean;
}
export class CognitoStack extends cdk.Stack {
    public readonly userPoolId: string;
    public readonly userPoolClientId: string;
    constructor(scope: Construct, id: string, props?: CognitoStackProps) {
        super(scope, id, props);

        // help me fix following code

        let signInAlisesOption = undefined
        let signInCaseSensitiveOption = undefined
        if (props?.sign_in_aliases_username) {
            signInAlisesOption =  { email: true, username: true, preferredUsername: true }
            signInCaseSensitiveOption = false
        } else {
            signInAlisesOption =  { email: true }
            signInCaseSensitiveOption = true // use default value
        }

        // Create a Cognito User Pool
        const userPool = new cognito.UserPool(this, 'GenBiUserPool', {
            userPoolName: 'GenBiUserPool',
            selfSignUpEnabled: true,
            signInAliases: signInAlisesOption,
            signInCaseSensitive: signInCaseSensitiveOption,
            autoVerify: { email: true },
            passwordPolicy: {
            minLength: 8,
            requireUppercase: false,
            requireLowercase: true,
            requireDigits: false,
            requireSymbols: false
        }
        });

        // Create a User Pool Client associated with the User Pool
        const userPoolClient = new cognito.UserPoolClient(this, 'GenBiUserPoolClient', {
        userPool: userPool,
        userPoolClientName: 'GenBiUserPoolClient'
        });

        this.userPoolId = userPool.userPoolId;
        this.userPoolClientId = userPoolClient.userPoolClientId;

        // Output the User Pool Id and User Pool Client Id
        new cdk.CfnOutput(this, 'UserPoolId', {
        value: userPool.userPoolId
        });

        new cdk.CfnOutput(this, 'UserPoolClientId', {
        value: userPoolClient.userPoolClientId
        });
    }
}