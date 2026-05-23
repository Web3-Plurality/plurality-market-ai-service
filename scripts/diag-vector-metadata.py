"""Inspect S3 Vectors metadata for specific vector keys, bypassing all filters.

Tells us definitively whether a vector exists at the given key and what
metadata it has (in particular, whether the `namespace` key is set).

Usage: python scripts/diag-vector-metadata.py <key1> [<key2> ...]
"""
import os
import sys
import json
import boto3

# Minimal .env loader so we don't depend on python-dotenv being installed.
def _load_env(path: str) -> None:
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            if k and k not in os.environ:
                os.environ[k] = v

_load_env(os.path.join(os.path.dirname(__file__), "..", ".env"))

keys = sys.argv[1:]
if not keys:
    print("Usage: python scripts/diag-vector-metadata.py <key1> [<key2> ...]")
    sys.exit(1)

client = boto3.client(
    "s3vectors",
    region_name=os.getenv("AWS_REGION", "us-east-2"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)

bucket = os.getenv("S3_VECTOR_BUCKET_NAME", "plurality-ocl")
index = os.getenv("S3_VECTOR_INDEX_NAME", "index")
print(f"Looking up {len(keys)} key(s) in bucket={bucket} index={index}\n")

resp = client.get_vectors(
    vectorBucketName=bucket,
    indexName=index,
    keys=keys,
    returnData=False,
    returnMetadata=True,
)

vectors = resp.get("vectors", [])
if not vectors:
    print("No vectors found at any of those keys.")
    sys.exit(0)

for v in vectors:
    print(f"key: {v.get('key')}")
    meta = v.get("metadata") or {}
    print(f"  metadata: {json.dumps(meta, indent=4)}")
    print(f"  has namespace key: {'namespace' in meta}")
    if "namespace" in meta:
        print(f"  namespace value: {meta['namespace']!r}")
    print()
