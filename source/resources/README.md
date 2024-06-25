## CDK Deployment Guide (Currently only support global region, China region will be added soon)
### 1. Prepare CDK Pre-requisites
Please follow the instructions in the [CDK Workshop](https://cdkworkshop.com/15-prerequisites.html) to install the CDK toolkit.

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
Deploy the CDK stack:
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
### 4. Access the Streamlit Web UI
After the CDK stack is deployed, wait around 40 minutes for the initialization to complete. Then, open the Streamlit Web UI in your browser: https://<your-public-dns>