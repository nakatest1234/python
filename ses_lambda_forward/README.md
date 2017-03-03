# REDADME

## flow
1. SES settings
  1. Email Receiving
  1. Rule Sets
  1. Action
  1. S3 (bucket, prefix)
1. Set S3 bucket Policy [S3 policy](#S3_policy)
1. Set lambda
  1. Create lambda(python2.7, Blank Function)
  1. S3 -> Lambda
  1. bucket=bucket, type=put, Prefix=<PREFIX>
  1. name, desc, Runtime=python2.7
  1. CODE
  1. [Environment variables](#lambda_env)
  1. [Role](#role)
  1. Timeout:10ms
1. S3 put lambda

## <a name="lambda_env"> lambda env

| env key | value |
| ------- | ----- |
| SES_REGION | for sendmail from SES |
| MAIL_FROM | sendmail from |
| MAIL_To | sendmail to(forward email address) |
| MAIL_SUBJECT | sendmail subject |

## <a name="S3_policy"> S3 policy
```
{
	"Version": "2008-10-17",
	"Statement": [
		{
			"Sid": "GiveSESPermissionToWriteEmail",
			"Effect": "Allow",
			"Principal": {
				"Service": "ses.amazonaws.com"
			},
			"Action": "s3:PutObject*",
			"Resource": "arn:aws:s3:::<BUCKET>/*",
			"Condition": {
				"StringEquals": {
					"aws:Referer": "<ACCOUNT_ID>"
				}
			}
		}
	]
}
```

## <a name="role"> role
* AWSLambdaBasicExecutionRole
* sendmail
```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ses:SendEmail",
                "ses:SendRawEmail"
            ],
            "Resource": "*"
        }
    ]
}
```
* get s3
```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject"
            ],
            "Resource": [
                "arn:aws:s3:::<BUCKET>/{PATH}/*"
            ]
        }
    ]
}
```
