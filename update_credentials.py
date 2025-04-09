import os
import re

def extract_and_save_from_file(filepath="aws_creds.txt"):
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        return

    with open(filepath, 'r') as file:
        raw = file.read()

    # Step 1: Extract values using regex
    access_key = re.search(r'aws_access_key_id\s*=\s*(\S+)', raw)
    secret_key = re.search(r'aws_secret_access_key\s*=\s*(\S+)', raw)
    session_token = re.search(r'aws_session_token\s*=\s*(.+)', raw, re.DOTALL)

    if not (access_key and secret_key and session_token):
        print("❌ Could not extract credentials. Check formatting.")
        return

    access_key = access_key.group(1)
    secret_key = secret_key.group(1)
    session_token = session_token.group(1).strip()

    # Step 2: Save to ~/.aws/credentials
    aws_path = os.path.expanduser("~/.aws")
    os.makedirs(aws_path, exist_ok=True)

    with open(os.path.join(aws_path, "credentials"), "w") as file:
        file.write(f"""[default]
aws_access_key_id={access_key}
aws_secret_access_key={secret_key}
aws_session_token={session_token}
""")
    print("✅ ~/.aws/credentials updated")

    # Step 3: Save to .env
    with open(".env", "w") as file:
        file.write(f"""AWS_ACCESS_KEY_ID={access_key}
AWS_SECRET_ACCESS_KEY={secret_key}
AWS_SESSION_TOKEN={session_token}
""")
    print("✅ .env updated")

if __name__ == "__main__":
    extract_and_save_from_file("aws_creds.txt")  # or any file name you prefer
