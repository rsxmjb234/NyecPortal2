"""Hello-world: read one object from S3 and print its first character."""
import boto3

PROFILE = "304507007699_AWSPowerUserAccess"
BUCKET = "nyec-synthetic-data"
KEY = "synthetic-ccda/BRONX-MPID-000004_Morris740_Yundt842_ce3ae025-2775-7bd4-234f-b6cb9724bbd9.xml"

session = boto3.Session(profile_name=PROFILE)
s3 = session.client("s3")

# Fetch only the first byte using a Range request, so we don't download the whole file.
resp = s3.get_object(Bucket=BUCKET, Key=KEY, Range="bytes=0-0")
first_byte = resp["Body"].read()
first_char = first_byte.decode("utf-8", errors="replace")

print(f"Bucket: {BUCKET}")
print(f"Key:    {KEY}")
print(f"First character: {first_char!r}")
