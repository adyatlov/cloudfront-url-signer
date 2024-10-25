# CloudFront URL Signer for Private S3 Static Websites

This script generates signed URLs for CloudFront distributions to control access to private S3-hosted static websites. You can use it to create temporary access URLs with expiration dates.

## Table of Contents

- [S3 Bucket Creation](#s3-bucket-creation)
- [Key Pair Generation](#key-pair-generation)
- [CloudFront Setup](#cloudfront-setup)
- [Using the URL Signer Script](#using-the-url-signer-script)

## S3 Bucket Creation

1. Go to S3 in AWS Console
2. ⚠️ Select your region in the top right corner first (changing it later will clear your bucket name)
3. Click "Create bucket"
4. Enter a unique bucket name
5. Keep all default settings
6. Click "Create bucket"
7. Upload your website files AND the `login.html` from this repository

[Screenshot placeholder: Create bucket dialog with default settings]

⚠️ **IMPORTANT:**

- Keep all default settings.
- Don not enable "Static website hosting"
- The `login.html` file is a part of this solution, not your website

## Key Pair Generation

### Create a Secure Directory for Keys

- Create a directory outside of any git repository

  ```bash
  mkdir cloudfront-keys
  cd cloudfront-keys
  ```

- Prevent git from tracking the files in this directory

  ```
  echo "*" > .gitignore
  ```

### Generate Key Pair

After creating your secure directory, run to create private and public keys:

```bash
openssl genrsa -out private_key.pem 2048 && openssl rsa -pubout -in private_key.pem -out public_key.pem
```

⚠️ **IMPORTANT SECURITY NOTES:**

- Create keys in a directory that sits outside any Git repository
- Never place keys in a directory that Git could track
- Use the private key only with the URL signer script
- Consider AWS KMS or a secure vault for key storage
- Rotate your keys regularly
- Run `chmod 600 private_key.pem` to restrict file access

## CloudFront Setup

### 1. Create Origin Access Control (OAC)

1. Go to CloudFront in AWS Console
2. Click "Security" → "Origin access" in the left menu
3. Click "Create control setting"
4. Enter a description (e.g., "<your-bucket-name>-OAC")
5. Set Origin type to "S3"
6. Keep default settings
7. Click "Create"

[Screenshot placeholder: Origin access control creation]

### 2. Create Key Group

1. Go to "Key Management" → "Public keys" in CloudFront
2. Click "Create public key"
3. Enter a name for your key (e.g., "my-static-website-key")
4. Copy content of the `public_key.pem` to the "Key" field. If you on MacOS, you can use the following command to copyt the key:
   ```bash
   pbcopy < public_key.pem
   ```
5. Click "Create"
6. Save the generated "Key ID" - you need it for the URL signer script
7. Go to "Key groups"
8. Click "Create key group"
9. Enter a group name (e.g., "my-static-website-key-group")
10. Select your uploaded public key
11. Click "Create key group"

[Screenshot placeholder: Key group creation dialog]

### 3. Create CloudFront Distribution

1. Go to the Distributions page in CloudFront
2. Click "Create distribution"
3. Under "Origin":
   - Pick your S3 bucket as Origin domain
   - Leave Origin path empty
   - Click on the "Origin access control settings (recommended)" radio button
   - Select your OAC in Origin access control dropdown
4. Under "Viewer":
   - Set the Restrict viewer access to "Yes"
   - In the "Add key groups" dropdown, select the key group you created in step 2
5. Under "Web Application Firewall (WAF)" choose whether or not you want to enable WAF
6. Click "Create distribution"

[Screenshot placeholder: CloudFront distribution creation with OAC]

### 5. Update Bucket Policy

Note, that the AWS CloudFront console can help you with the following steps by generating the policy and providing a link to the the right place in the S3 console.

1. Go to your S3 bucket
2. Click "Permissions" tab
3. Click "Edit" under "Bucket policy"
4. Add this policy (replace the placeholders):

```json
{
  "Version": "2012-10-17",
  "Id": "PolicyForCloudFrontPrivateContent",
  "Statement": [
    {
      "Sid": "AllowCloudFrontServicePrincipal",
      "Effect": "Allow",
      "Principal": {
        "Service": "cloudfront.amazonaws.com"
      },
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::<your-bucket-name>/*",
      "Condition": {
        "StringEquals": {
          "AWS:SourceArn": "arn:aws:cloudfront::<your-account-id>:distribution/<your-distribution-id>"
        }
      }
    }
  ]
}
```

## Using the URL Signer Script

### Environment Setup

```bash
python3 -m venv myenv
source myenv/bin/activate
pip3 install -r requirements.txt
```

### Script Usage

```bash
python3 cloudfront_url_signer.py <private-key-path> <key-id> <expiration-days> <distribution-domain> <redirect-path>
```

### Parameters

- `private-key-path`: Where to find your private key file (.pem)
- `key-id`: Your key pair ID from CloudFront
- `expiration-days`: How many days the URL should work
- `distribution-domain`: Your CloudFront domain (e.g., `d1234.cloudfront.net`)
- `redirect-path`: Where to go after login (e.g., `/index.html`)

### Example

```bash
python cloudfront_url_signer.py ./private_key.pem K2JCJMDEHXQW5F 7 d1234.cloudfront.net /dashboard.html
```

This command creates a signed URL using:

- The private key from `./private_key.pem`
- Key pair ID `K2JCJMDEHXQW5F`
- 7-day validity
- Distribution `d1234.cloudfront.net`
- Redirect to `/dashboard.html` after login

### Output

The script creates a URL like this:

```
https://d1234.cloudfront.net/login.html?Policy=eyJTdGF0...&Signature=ABCdef...&Key-Pair-Id=K2JCJMDEHXQW5F&Expires=1234567890&RedirectTo=/dashboard.html
```
