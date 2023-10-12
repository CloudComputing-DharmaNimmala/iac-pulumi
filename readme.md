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

