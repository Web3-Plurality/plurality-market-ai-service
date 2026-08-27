# Context Service Migration to Amazon S3 Vectors

This context service has been migrated from Pinecone to **Amazon S3 Vectors**, AWS's native vector storage solution. S3 Vectors provides serverless, scalable vector storage with seamless AWS integration.

## What's New

### From Pinecone to S3 Vectors
- **Native AWS Integration**: No third-party dependencies
- **Cost-Effective**: Pay only for what you use
- **Serverless**: No infrastructure management required
- **High Performance**: Optimized for AWS workloads

### From Google Embeddings to BGE
- **Better Performance**: BAAI/bge-large-en-v1.5 offers superior retrieval quality
- **Open Source**: No vendor lock-in
- **1024 dimensions**: More detailed embeddings than previous 768-dim model

## Prerequisites

1. **AWS Account** with appropriate permissions
2. **AWS CLI** configured
3. **Python 3.11+**
4. **Google API Key** (for Gemini LLM)

## Environment Variables

Create a `.env` file with the following variables:

```env
# API Security
CONTEXT_API_KEY=your-secure-api-key-here

# Google AI (for LLM only)
GOOGLE_API_KEY=your-google-api-key-here

# AWS Configuration
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_REGION=us-east-1

# S3 Vectors Configuration
S3_VECTOR_BUCKET_NAME=notebook-context-vectors
S3_VECTOR_INDEX_NAME=notebook-context-index
```

## AWS Permissions Required

Your AWS IAM user/role needs the following permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3vectors:CreateVectorBucket",
                "s3vectors:DescribeVectorBucket",
                "s3vectors:CreateVectorIndex",
                "s3vectors:DescribeVectorIndex",
                "s3vectors:PutVectors",
                "s3vectors:QueryVectors",
                "s3vectors:ListVectorIndexes"
            ],
            "Resource": "*"
        }
    ]
}
```

## Installation

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Run the service**:
   ```bash
   uvicorn app.main:app --port 8001 --reload
   ```

## Key Features

### Automatic Setup
- Vector bucket and index are created automatically on first run
- No manual infrastructure setup required

### Optimized Configuration
- **Dimension**: 1024 (optimized for BGE-large-en-v1.5)
- **Distance Metric**: Cosine similarity
- **Encryption**: SSE-S3 (S3-managed keys)

### Enhanced Metadata
- Content stored as non-filterable metadata for retrieval
- User and profile filtering for multi-tenant support
- File type and source tracking

### Supported File Types
- **TXT**: Plain text files
- **DOCX**: Microsoft Word documents
- **PDF**: Portable Document Format files
- **MD/Markdown**: Markdown formatted files with fallback support
- **JSON**: JavaScript Object Notation files (converts structured data to searchable text)

## API Usage

All endpoints live under the `/rag` prefix on port **8001**:

### Upload File
```bash
curl -X POST "http://localhost:8001/rag/upload-file" \
  -H "X-API-Key: your-api-key" \
  -F "file=@document.json" \
  -F "userId=user123" \
  -F "profileId=profile456" \
  -F "contextId=context789"
```

### Add Context
```bash
curl -X POST "http://localhost:8001/rag/add-context" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "user123",
    "profileId": "profile456",
    "contextId": "context789",
    "context": "Your context content here"
  }'
```

### Similarity Search
```bash
curl -X POST "http://localhost:8001/rag/similarity-search" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "user123",
    "profileId": "profile456",
    "query": "What is machine learning?",
    "k": 5
  }'
```

## Migration Notes

### What Changed
1. **Vector Storage**: Pinecone → Amazon S3 Vectors
2. **Embeddings**: Google Embeddings → BGE-large-en-v1.5
3. **Dependencies**: Removed pinecone-client, added boto3
4. **Configuration**: New AWS-based environment variables

### What Stayed the Same
- All API endpoints and request/response formats
- File processing capabilities (PDF, DOCX, TXT, MD, JSON)
- Multi-tenant user/profile filtering
- Automatic title extraction with LLM

### Performance Improvements
- **Faster embeddings**: BGE model is optimized for retrieval
- **Lower latency**: Native AWS integration reduces network overhead
- **Better scaling**: S3 Vectors automatically scales with your data

## Troubleshooting

### Common Issues

1. **"NoSuchVectorBucket" Error**
   - Ensure AWS credentials are configured
   - Check AWS region matches your configuration
   - Verify S3 Vectors is available in your region

2. **"Access Denied" Error**
   - Check IAM permissions
   - Ensure S3 Vectors permissions are attached to your user/role

3. **Embedding Model Download**
   - First run will download BGE model (~1.3GB)
   - Ensure stable internet connection
   - Model is cached locally after first download

### Supported Regions

S3 Vectors is currently available in these regions:
- us-east-1 (N. Virginia)
- us-west-2 (Oregon)
- eu-west-1 (Ireland)

Check [AWS documentation](https://docs.aws.amazon.com/AmazonS3/latest/userguide/s3-vectors-getting-started.html) for the latest region availability.

## Cost Optimization

### S3 Vectors Pricing
- **Storage**: ~$0.023 per GB per month
- **Operations**: Per-request pricing for PUT/GET/QUERY
- **No minimum charges**: Pay only for what you use

### BGE Model
- **One-time download**: ~1.3GB model file
- **Local inference**: No per-request costs
- **GPU optional**: Works on CPU (slower) or GPU (faster)

## Support

For issues specific to:
- **S3 Vectors**: Check [AWS S3 Vectors Documentation](https://docs.aws.amazon.com/AmazonS3/latest/userguide/s3-vectors-getting-started.html)
- **BGE Embeddings**: See [Hugging Face Model Page](https://huggingface.co/BAAI/bge-large-en-v1.5)
- **This Service**: Open an issue in this repository 