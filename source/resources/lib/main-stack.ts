import { Duration, Stack, StackProps, CfnOutput } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { Ec2Stack } from './ec2/ec2-stack';

export class MainStack extends Stack {
  constructor(scope: Construct, id: string, props: StackProps = {}) {
    super(scope, id, props);

    const _Ec2Stack = new Ec2Stack(this, 'ec2-Stack', {
      env: props.env,
    });

    new CfnOutput(this, 'Ec2PublicIP', {
      value: _Ec2Stack._publicIP,
      description: 'Public IP of the EC2 instance',
    });
  }
}
