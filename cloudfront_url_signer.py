import json
import base64
import sys
from datetime import datetime, timedelta, timezone
from urllib.parse import quote_plus, quote
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes

def rsa_signer(key_file, message):
    with open(key_file, 'rb') as key_file:
        private_key = load_pem_private_key(
            key_file.read(),
            password=None
        )
    signature = private_key.sign(
        message,
        padding.PKCS1v15(),
        hashes.SHA1()
    )
    return signature

def generate_signed_url(key_file, key_id, expiration, url, redirect_path):
    expires = datetime.now(timezone.utc) + timedelta(days=int(expiration))
    epoch_expiration = int(expires.timestamp())
    resource = url + "/*"

    # Build the custom policy
    policy = {
        "Statement": [
            {
                "Resource": resource,
                "Condition": {
                    "DateLessThan": {
                        "AWS:EpochTime": epoch_expiration
                    }
                }
            }
        ]
    }

    # Convert policy to JSON string without spaces
    policy_json = json.dumps(policy, separators=(',', ':'))

    # Sign the policy
    policy_bytes = policy_json.encode('utf-8')
    signature = rsa_signer(key_file, policy_bytes)

    # Base64-encode the policy and signature
    encoded_policy = base64.b64encode(policy_bytes).decode('utf-8')
    encoded_signature = base64.b64encode(signature).decode('utf-8')

    # URL-encode the policy and signature
    encoded_policy = quote_plus(encoded_policy)
    encoded_signature = quote_plus(encoded_signature)

    # Encode expiration 
    encoded_expiration = str(epoch_expiration)

    # Encode redirect_path
    encoded_redirect_path = quote(redirect_path, safe='')

    # Construct the signed URL
    signed_url = f"{url}/login.html?Policy={encoded_policy}&Signature={encoded_signature}&Key-Pair-Id={key_id}&Expires={encoded_expiration}&RedirectTo={encoded_redirect_path}"

    return signed_url

if __name__ == "__main__":
    if len(sys.argv) != 6:
        print("Please specify path to private key, key id, expiration in days, distribution domain name, and redirect path as parameters.\n")
        exit(1)
    key_file = sys.argv[1]
    key_id = sys.argv[2]
    expiration = sys.argv[3]
    url = sys.argv[4]
    redirect_path = sys.argv[5]
    signed_url = generate_signed_url(key_file, key_id, expiration, url, redirect_path)
    print(signed_url)
