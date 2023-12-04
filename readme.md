# Assignment 4
---
##### git clone git@github.com:NimmalaD/iac-pulumi.git
---
#### Installations required
- Install AWS-CLI
```
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
sudo installer -pkg ./AWSCLIV2.pkg -target /
```
- Install Pulumi

```
brew install pulumi/tap/pulumi
pip install pulumi-aws
```

- Select Stacks
- Dev
```
pulumi stack select dev
```
- Demo
```
pulumi stack select demo
```
- Create Infrastructure
```
pulumi up
```
- Destroy Infrastructure
```
pulumi destroy
```
### Import SSL Certificate from Namecheap AWS Certificate Manager using AWS CLI
```
aws acm import-certificate --profile demo --certificate fileb://demo_mynscc_me.crt --certificate-chain fileb://demo_mynscc_me.ca-bundle --private-key fileb://private.key --region us-west-1
```

