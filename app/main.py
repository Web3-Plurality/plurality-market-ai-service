from fastapi import FastAPI, Response
from app.api.context_routes import context_router
from app.middleware.metrics_middleware import PrometheusMiddleware
from app.services.metrics_service import get_metrics

# Initialize FastAPI
app = FastAPI(
    title="Plurality AI Context Service",
    description="A comprehensive RAG (Retrieval-Augmented Generation) service for managing and querying personal knowledge bases",
    version="1.0.0"
)

# Add Prometheus middleware
app.add_middleware(PrometheusMiddleware)

# Include routers
app.include_router(context_router)

# Metrics endpoint for Prometheus
@app.get("/metrics")
async def metrics():
    """Expose Prometheus metrics"""
    return Response(content=get_metrics(), media_type="text/plain")



# from fastapi import UploadFile, File, HTTPException
# from fastapi.responses import JSONResponse
# from typing import Optional
# from pydantic import BaseModel
# import os
# from langchain_google_genai import GoogleGenerativeAI
# from langchain_pinecone import PineconeVectorStore
# from langchain.text_splitter import RecursiveCharacterTextSplitter
# from langchain_google_genai import GoogleGenerativeAIEmbeddings
# from langchain_community.document_loaders import TextLoader
# from pinecone import Pinecone, ServerlessSpec
# import tempfile
# from datetime import datetime
# import time
# import uuid

# Initialize Pinecone
# pinecone = Pinecone(
#     api_key=os.getenv("PINECONE_API_KEY")
# )

# # Initialize Google embeddings
# embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=os.getenv("GOOGLE_API_KEY"))
# # Initialize Gemini
# llm = GoogleGenerativeAI(model="gemini-2.0-flash-exp",api_key=os.getenv("GOOGLE_API_KEY"))

# # Initialize vector store
# index_name = "plurality-index"
# if not any(index.name == index_name for index in pinecone.list_indexes()):
#     pinecone.create_index(
#         name=index_name,
#         metric='cosine',
#         dimension=768,  # dimension for Google Palm embeddings
#         spec=ServerlessSpec(
#         cloud="aws",
#         region="us-east-1"
#         )
#     )

# vector_store = PineconeVectorStore(
#     index_name=index_name,
#     embedding=embeddings
# )

# class QueryRequest(BaseModel):
#     query: str
#     userId: Optional[str] = None  # Make userId optional to maintain backward compatibility
#     app: Optional[str] = None     # Add app filter to distinguish between TikTok/Twitter

# # Add this new Pydantic model for text input
# class TextInput(BaseModel):
#     text: str
#     metadata: dict = {}  # Optional metadata for the document

# Add these new Pydantic models
# class TikTokUser(BaseModel):
#     display_name: str
#     follower_count: int
#     following_count: int
#     is_verified: bool
#     likes_count: int
#     profile_deep_link: str
#     username: str
#     bio_description: str
#     video_count: int
#     open_id: str
#     union_id: str
#     avatar_url: str

# class TikTokVideo(BaseModel):
#     title: str
#     view_count: int
#     comment_count: int
#     height: int
#     share_count: int
#     create_time: int
#     embed_link: str
#     video_description: str
#     cover_image_url: str
#     duration: int
#     like_count: int
#     id: str
#     share_url: str
#     width: int

# class TikTokData(BaseModel):
#     user: TikTokUser
#     videos: list[TikTokVideo]
#     userId: str  # Added for user identification
#     app: str = "tiktok"  # Default value for app

# class TwitterPublicMetrics(BaseModel):
#     followers_count: int
#     following_count: int
#     tweet_count: int
#     listed_count: int
#     like_count: int
#     media_count: int

# class TwitterUserData(BaseModel):
#     most_recent_tweet_id: str
#     pinned_tweet_id: Optional[str] = None
#     verified: bool
#     created_at: str
#     username: str
#     public_metrics: TwitterPublicMetrics
#     id: str
#     name: str
#     description: str
#     profile_image_url: str
#     location: Optional[str]
#     verified_type: str
#     protected: bool

# class Tweet(BaseModel):
#     username: str
#     Views: str
#     date: str
#     tweetText: str
#     tweet_id: str

# class TwitterData(BaseModel):
#     data: TwitterUserData
#     userId: str
#     app: str = "twitter"
#     new_tweet: Optional[Tweet] = None
#     pinned_tweet: Optional[Tweet] = None

# Roblox Models
# class RobloxAssetDetails(BaseModel):
#     assetId: str
#     inventoryItemAssetType: str
#     instanceId: str

# class RobloxInventoryItem(BaseModel):
#     path: str
#     assetDetails: RobloxAssetDetails
#     addTime: str

# class RobloxUser(BaseModel):
#     sub: str  # Roblox user ID
#     created_at: int
#     picture: str
#     name: str
#     nickname: str
#     preferred_username: str
#     profile: str
#     displayName: str
#     about: str
#     inventoryItems: list[RobloxInventoryItem]
#     joinDate: str = ""
#     placesVisit: int = 0
#     friends: int = 0
#     followers: int = 0
#     following: int = 0
#     avatar: str

# class RobloxData(BaseModel):
#     profile: RobloxUser
#     userId: str  # For consistency with other models
#     app: str = "roblox"  # Default value for app

# Reddit Models
# class RedditKarma(BaseModel):
#     comment: int
#     link: int
#     total: int

# class RedditPost(BaseModel):
#     id: str
#     title: str
#     subreddit: str
#     score: int
#     created: int
#     permalink: str
#     url: str
#     text: str

# class RedditComment(BaseModel):
#     id: str
#     subreddit: str
#     score: int
#     created: int
#     text: str

# class RedditTrophy(BaseModel):
#     name: str
#     description: Optional[str] = None
#     icon: str

# class RedditProfile(BaseModel):
#     name: str
#     karma: RedditKarma
#     created: int
#     verified: bool
#     posts: list[RedditPost]
#     comments: list[RedditComment]
#     trophies: list[RedditTrophy]
#     subreddits: list[str]

# class RedditData(BaseModel):
#     profile: RedditProfile
#     userId: str  # For consistency with other models
#     app: str = "reddit"  # Default value for app

# Spotify Models
# class SpotifyArtist(BaseModel):
#     followers: int
#     genres: list[str]
#     name: str
#     id: str
#     popularity: int
#     type: str
#     url: str

# class SpotifyPlaylist(BaseModel):
#     description: str
#     url: str
#     name: str
#     id: str

# class SpotifyFollowing(BaseModel):
#     followers: int
#     genres: list[str]
#     name: str
#     id: str
#     popularity: int
#     type: str
#     url: str

# class SpotifySavedShow(BaseModel):
#     added_at: str
#     publisher: str
#     type: str
#     languages: list[str]
#     name: str
#     description: str
#     id: str
#     total_episodes: int
#     url: str

# class SpotifyAudiobook(BaseModel):
#     authors: list[str]
#     available_markets: list[str]
#     publisher: str
#     type: str
#     languages: list[str]
#     name: str
#     description: str
#     id: str

# class SpotifyProfile(BaseModel):
#     country: str
#     displayName: str
#     email: str
#     profile: str
#     topArtists: list[SpotifyArtist] = []
#     playlists: list[SpotifyPlaylist] = []
#     following: list[SpotifyFollowing] = []
#     savedShows: list[SpotifySavedShow] = []
#     audiobooks: list[SpotifyAudiobook] = []

# class SpotifyData(BaseModel):
#     profile: SpotifyProfile
#     userId: str  # For consistency with other models
#     app: str = "spotify"  # Default value for app

# GitHub Models
# class GitHubRepository(BaseModel):
#     id: int
#     name: str
#     description: Optional[str] = None
#     language: Optional[str] = None
#     topics: list[str] = []
#     stargazers_count: int

# class GitHubProfile(BaseModel):
#     name: str
#     login: str
#     avatar: str
#     email: str
#     bio: str
#     location: str
#     followers: int
#     following: int
#     publicRepos: int
#     publicGists: int
#     createdAt: str
#     updatedAt: str
#     repositories: list[GitHubRepository] = []

# class GitHubData(BaseModel):
#     profile: GitHubProfile
#     userId: str  # For consistency with other models
#     app: str = "github"  # Default value for app

# Add this new Pydantic model for custom context input
# class CustomContextInput(BaseModel):
#     text: str
#     userId: str  # Required user ID for filtering
#     context_type: Optional[str] = "custom"  # Type of context (custom, note, preference, etc.)
#     title: Optional[str] = None  # Optional title for the context
#     metadata: dict = {}  # Additional metadata



# @app.post("/upload")
# async def upload_document(file: UploadFile = File(...)):
#     """
#     Upload a text document to be processed and stored in the vector database
#     """
#     try:
#         # Read file content
#         content = await file.read()
#         # Decode content assuming UTF-8 encoding
#         text_content = content.decode('utf-8')
        
#         # Split text into chunks
#         text_splitter = RecursiveCharacterTextSplitter(
#             chunk_size=1000,
#             chunk_overlap=200
#         )
        
#         # Create splits directly from text
#         splits = text_splitter.create_documents(
#             texts=[text_content],
#             metadatas=[{"source": file.filename}]
#         )
        
#         # Store in vector database
#         vector_store.add_documents(splits)
        
#         return JSONResponse(
#             content={
#                 "message": f"Successfully processed and stored document: {file.filename}",
#                 "chunks": len(splits)
#             },
#             status_code=200
#         )
    
#     except UnicodeDecodeError:
#         raise HTTPException(
#             status_code=400,
#             detail="File encoding not supported. Please upload a UTF-8 encoded text file."
#         )
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @app.post("/add-text")
# async def add_text(text_input: TextInput):
#     """
#     Add text directly to the vector database
#     """
#     try:
#         # Split text into chunks
#         text_splitter = RecursiveCharacterTextSplitter(
#             chunk_size=1000,
#             chunk_overlap=200
#         )
        
#         # Create splits from the text
#         splits = text_splitter.create_documents(
#             texts=[text_input.text],
#             metadatas=[text_input.metadata]
#         )
        
#         # Store in vector database
#         vector_store.add_documents(splits)
        
#         return JSONResponse(
#             content={
#                 "message": "Successfully processed and stored text",
#                 "chunks": len(splits)
#             },
#             status_code=200
#         )
    
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @app.post("/query")
# async def query_documents(request: QueryRequest):
#     """
#     Query the RAG system with a question, optionally filtered by userId and app
#     """
#     try:
#         # Prepare filter based on provided parameters
#         filter_dict = {}
#         if request.userId:
#             filter_dict["userId"] = request.userId
#         if request.app:
#             filter_dict["app"] = request.app

#         # Search for relevant documents with filter
#         relevant_docs = vector_store.similarity_search(
#             request.query,
#             k=3,  # Number of relevant documents to retrieve
#             filter=filter_dict if filter_dict else None
#         )
        
#         # Prepare context from relevant documents
#         context = "\n\n".join([doc.page_content for doc in relevant_docs])
        
#         # Prepare prompt
#         prompt = f"""
#         Use the following context and your own knowledge, please answer the questions. 
        
#         Context: {context}
        
#         Question: {request.query}
        
#         Answer:"""
        
#         # Generate response
#         response = llm.invoke(prompt)
        
#         return {
#             "answer": response,
#             "sources": [doc.page_content for doc in relevant_docs],
#             "filtered_by": {
#                 "userId": request.userId if request.userId else "none",
#                 "app": request.app if request.app else "none"
#             }
#         }
    
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @app.post("/add-tiktok-data")
# async def add_tiktok_data(tiktok_data: TikTokData):
#     """
#     Add TikTok user and video data to the vector database using Pinecone's upsert functionality
#     """
#     try:
#         # Process user profile
#         user_identifier = f"tiktok_profile_{tiktok_data.userId}"
#         user_text = f"""
#         TikTok Profile:
#         Username: {tiktok_data.user.username}
#         Display Name: {tiktok_data.user.display_name}
#         Bio: {tiktok_data.user.bio_description}
#         Followers: {tiktok_data.user.follower_count}
#         Following: {tiktok_data.user.following_count}
#         Likes: {tiktok_data.user.likes_count}
#         Videos: {tiktok_data.user.video_count}
#         """
        
#         # Create metadata for user profile
#         user_metadata = {
#             "userId": tiktok_data.userId,
#             "app": tiktok_data.app,
#             "content_type": "profile",
#             "last_updated": int(time.time())
#         }
        
#         # Initialize documents and IDs lists
#         documents_to_upsert = []
#         document_ids = []
        
#         # Split and store all content
#         text_splitter = RecursiveCharacterTextSplitter(
#             chunk_size=1000,
#             chunk_overlap=200
#         )
        
#         # Process user profile
#         user_splits = text_splitter.create_documents(
#             texts=[user_text],
#             metadatas=[user_metadata]
#         )
#         documents_to_upsert.extend(user_splits)
#         document_ids.extend([user_identifier] * len(user_splits))
        
#         # Process videos
#         for video in tiktok_data.videos:
#             video_identifier = f"tiktok_video_{tiktok_data.userId}_{video.id}"
#             video_text = f"""
#             Video Title: {video.title}
#             Description: {video.video_description}
#             Views: {video.view_count}
#             Likes: {video.like_count}
#             Comments: {video.comment_count}
#             Shares: {video.share_count}
#             Created at: {video.create_time}
#             """
            
#             video_metadata = {
#                 "userId": tiktok_data.userId,
#                 "app": tiktok_data.app,
#                 "content_type": "video",
#                 "video_id": video.id,
#                 "last_updated": int(time.time())
#             }
            
#             video_splits = text_splitter.create_documents(
#                 texts=[video_text],
#                 metadatas=[video_metadata]
#             )
#             documents_to_upsert.extend(video_splits)
#             document_ids.extend([video_identifier] * len(video_splits))
        
#         # Upsert all documents using Pinecone's native upsert functionality
#         if documents_to_upsert:
#             vector_store.add_documents(documents_to_upsert, ids=document_ids)
        
#         return JSONResponse(
#             content={
#                 "message": f"Successfully upserted TikTok data for user {tiktok_data.user.username}",
#                 "profile_updated": True,
#                 "videos_processed": len(tiktok_data.videos),
#                 "total_chunks": len(documents_to_upsert)
#             },
#             status_code=200
#         )
    
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @app.post("/add-twitter-data")
# async def add_twitter_data(twitter_data: TwitterData):
#     """
#     Add Twitter user data and tweets to the vector database using upsert
#     """
#     try:
#         # Process user profile
#         user_identifier = f"twitter_profile_{twitter_data.data.id}"
#         user_text = f"""
#         Twitter Profile:
#         Username: {twitter_data.username}
#         Name: {twitter_data.data.name}
#         Bio: {twitter_data.data.description}
#         Location: {twitter_data.data.location or 'Not specified'}
#         Followers: {twitter_data.data.public_metrics.followers_count}
#         Following: {twitter_data.data.public_metrics.following_count}
#         Tweets: {twitter_data.data.public_metrics.tweet_count}
#         Likes: {twitter_data.data.public_metrics.like_count}
#         Listed Count: {twitter_data.data.public_metrics.listed_count}
#         Media Count: {twitter_data.data.public_metrics.media_count}
#         Account Created: {twitter_data.data.created_at}
#         Verified: {twitter_data.data.verified}
#         Verified Type: {twitter_data.data.verified_type}
#         Protected: {twitter_data.data.protected}
#         description: {twitter_data.data.description}
#         """
        
#         user_metadata = {
#             "userId": twitter_data.userId,
#             "app": twitter_data.app,
#             "content_type": "profile",
#             "document_id": user_identifier,
#             "platform_user_id": twitter_data.data.id,
#             "last_updated": int(time.time())
#         }

#         # Initialize documents list with user profile
#         documents_to_upsert = []
#         document_ids = []

#         # Split user profile
#         text_splitter = RecursiveCharacterTextSplitter(
#             chunk_size=1000,
#             chunk_overlap=200
#         )
        
#         user_splits = text_splitter.create_documents(
#             texts=[user_text],
#             metadatas=[user_metadata]
#         )
#         documents_to_upsert.extend(user_splits)
#         document_ids.extend([user_identifier] * len(user_splits))

#         # Process new tweet if provided
#         if twitter_data.new_tweet:
#             tweet_identifier = f"twitter_tweet_{twitter_data.data.most_recent_tweet_id}"
#             tweet_text = f"""
#             Tweet:
#             Username: {twitter_data.new_tweet.username}
#             Content: {twitter_data.new_tweet.tweetText}
#             Views: {twitter_data.new_tweet.Views}
#             Posted at: {twitter_data.new_tweet.date}
#             """
            
#             tweet_metadata = {
#                 "userId": twitter_data.userId,
#                 "app": twitter_data.app,
#                 "content_type": "tweet",
#                 "document_id": tweet_identifier,
#                 "tweet_id": twitter_data.new_tweet.tweet_id,
#                 "is_pinned": False,
#                 "last_updated": int(time.time())
#             }
            
#             tweet_splits = text_splitter.create_documents(
#                 texts=[tweet_text],
#                 metadatas=[tweet_metadata]
#             )
#             documents_to_upsert.extend(tweet_splits)
#             document_ids.extend([tweet_identifier] * len(tweet_splits))

#         # Process pinned tweet if provided
#         if twitter_data.pinned_tweet:
#             pinned_tweet_identifier = f"twitter_tweet_{twitter_data.data.pinned_tweet_id}"
#             pinned_tweet_text = f"""
#             Pinned Tweet:
#             Username: {twitter_data.pinned_tweet.username}
#             Content: {twitter_data.pinned_tweet.tweetText}
#             Views: {twitter_data.pinned_tweet.Views}
#             Posted at: {twitter_data.pinned_tweet.date}
#             """
            
#             pinned_tweet_metadata = {
#                 "userId": twitter_data.userId,
#                 "app": twitter_data.app,
#                 "content_type": "tweet",
#                 "document_id": pinned_tweet_identifier,
#                 "tweet_id": twitter_data.pinned_tweet.tweet_id,
#                 "is_pinned": True,
#                 "last_updated": int(time.time())
#             }
            
#             pinned_tweet_splits = text_splitter.create_documents(
#                 texts=[pinned_tweet_text],
#                 metadatas=[pinned_tweet_metadata]
#             )
#             documents_to_upsert.extend(pinned_tweet_splits)
#             document_ids.extend([pinned_tweet_identifier] * len(pinned_tweet_splits))

#         # Upsert all documents
#         if documents_to_upsert:
#             vector_store.add_documents(documents_to_upsert, ids=document_ids)

#         return JSONResponse(
#             content={
#                 "message": f"Successfully processed Twitter data for user {twitter_data.data.username}",
#                 "profile_updated": True,
#                 "new_tweet_added": bool(twitter_data.new_tweet),
#                 "pinned_tweet_updated": bool(twitter_data.pinned_tweet),
#                 "total_chunks": len(documents_to_upsert)
#             },
#             status_code=200
#         )
    
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @app.post("/add-roblox-data")
# async def add_roblox_data(roblox_data: RobloxData):
#     """
#     Add Roblox user data and inventory items to the vector database using upsert
#     """
#     try:
#         # Process user profile
#         user_identifier = f"roblox_profile_{roblox_data.userId}"
#         user_text = f"""
#         Roblox Profile:
#         Username: {roblox_data.profile.name}
#         Display Name: {roblox_data.profile.displayName}
#         About: {roblox_data.profile.about}
#         Created At: {datetime.fromtimestamp(roblox_data.profile.created_at).strftime('%Y-%m-%d %H:%M:%S')}
#         Profile URL: {roblox_data.profile.profile}
#         Places Visited: {roblox_data.profile.placesVisit}
#         Friends: {roblox_data.profile.friends}
#         Followers: {roblox_data.profile.followers}
#         Following: {roblox_data.profile.following}
#         """
#         # Create metadata for user profile
#         user_metadata = {
#             "userId": roblox_data.userId,
#             "app": roblox_data.app,
#             "content_type": "profile",
#             "platform_user_id": roblox_data.profile.sub,
#             "last_updated": int(time.time())
#         }
        
#         # Initialize documents and IDs lists
#         documents_to_upsert = []
#         document_ids = []
        
#         # Split and store user content
#         text_splitter = RecursiveCharacterTextSplitter(
#             chunk_size=5000,
#             chunk_overlap=200
#         )
        
#         # Process user profile
#         user_splits = text_splitter.create_documents(
#             texts=[user_text],
#             metadatas=[user_metadata]
#         )
#         documents_to_upsert.extend(user_splits)
#         document_ids.extend([user_identifier] * len(user_splits))
        
#         # Process inventory items
#         for item in roblox_data.profile.inventoryItems:
#             item_identifier = f"roblox_item_{roblox_data.userId}_{item.assetDetails.instanceId}"
            
#             item_text = f"""
#             Inventory Item:
#             Type: {item.assetDetails.inventoryItemAssetType}
#             Asset ID: {item.assetDetails.assetId}
#             Instance ID: {item.assetDetails.instanceId}
#             Added On: {item.addTime}
#             """
            
#             item_metadata = {
#                 "userId": roblox_data.userId,
#                 "app": roblox_data.app,
#                 "content_type": "inventory_item",
#                 "asset_id": item.assetDetails.assetId,
#                 "asset_type": item.assetDetails.inventoryItemAssetType,
#                 "instance_id": item.assetDetails.instanceId,
#                 "last_updated": int(time.time())
#             }
            
#             item_splits = text_splitter.create_documents(
#                 texts=[item_text],
#                 metadatas=[item_metadata]
#             )
#             documents_to_upsert.extend(item_splits)
#             document_ids.extend([item_identifier] * len(item_splits))
        
#         # Upsert all documents
#         if documents_to_upsert:
#             vector_store.add_documents(documents_to_upsert, ids=document_ids)
        
#         return JSONResponse(
#             content={
#                 "message": f"Successfully upserted Roblox data for user {roblox_data.profile.name}",
#                 "profile_updated": True,
#                 "inventory_items_processed": len(roblox_data.profile.inventoryItems),
#                 "total_chunks": len(documents_to_upsert)
#             },
#             status_code=200
#         )
    
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @app.post("/add-reddit-data")
# async def add_reddit_data(reddit_data: RedditData):
#     """
#     Add Reddit user data, posts, comments, and trophies to the vector database using upsert
#     """
#     try:
#         # Process user profile
#         user_identifier = f"reddit_profile_{reddit_data.userId}"
#         user_text = f"""
#         Reddit Profile:
#         Username: {reddit_data.profile.name}
#         Total Karma: {reddit_data.profile.karma.total}
#         Comment Karma: {reddit_data.profile.karma.comment}
#         Link Karma: {reddit_data.profile.karma.link}
#         Account Created: {datetime.fromtimestamp(reddit_data.profile.created).strftime('%Y-%m-%d %H:%M:%S')}
#         Verified: {reddit_data.profile.verified}
#         Subreddits: {', '.join(reddit_data.profile.subreddits)}
#         """
        
#         # Create metadata for user profile
#         user_metadata = {
#             "userId": reddit_data.userId,
#             "app": reddit_data.app,
#             "content_type": "profile",
#             "platform_user_id": reddit_data.profile.name,
#             "last_updated": int(time.time())
#         }
        
#         # Initialize documents and IDs lists
#         documents_to_upsert = []
#         document_ids = []
        
#         # Split and store user content
#         text_splitter = RecursiveCharacterTextSplitter(
#             chunk_size=5000,
#             chunk_overlap=200
#         )
        
#         # Process user profile
#         user_splits = text_splitter.create_documents(
#             texts=[user_text],
#             metadatas=[user_metadata]
#         )
#         documents_to_upsert.extend(user_splits)
#         document_ids.extend([user_identifier] * len(user_splits))
        
#         # Process posts
#         for post in reddit_data.profile.posts:
#             post_identifier = f"reddit_post_{reddit_data.userId}_{post.id}"
#             post_text = f"""
#             Reddit Post:
#             Title: {post.title}
#             Subreddit: {post.subreddit}
#             Score: {post.score}
#             Created: {datetime.fromtimestamp(post.created).strftime('%Y-%m-%d %H:%M:%S')}
#             Content: {post.text}
#             URL: {post.url}
#             """
            
#             post_metadata = {
#                 "userId": reddit_data.userId,
#                 "app": reddit_data.app,
#                 "content_type": "post",
#                 "post_id": post.id,
#                 "subreddit": post.subreddit,
#                 "last_updated": int(time.time())
#             }
            
#             post_splits = text_splitter.create_documents(
#                 texts=[post_text],
#                 metadatas=[post_metadata]
#             )
#             documents_to_upsert.extend(post_splits)
#             document_ids.extend([post_identifier] * len(post_splits))
        
#         # Process comments
#         for comment in reddit_data.profile.comments:
#             comment_identifier = f"reddit_comment_{reddit_data.userId}_{comment.id}"
#             comment_text = f"""
#             Reddit Comment:
#             Subreddit: {comment.subreddit}
#             Score: {comment.score}
#             Created: {datetime.fromtimestamp(comment.created).strftime('%Y-%m-%d %H:%M:%S')}
#             Content: {comment.text}
#             """
            
#             comment_metadata = {
#                 "userId": reddit_data.userId,
#                 "app": reddit_data.app,
#                 "content_type": "comment",
#                 "comment_id": comment.id,
#                 "subreddit": comment.subreddit,
#                 "last_updated": int(time.time())
#             }
            
#             comment_splits = text_splitter.create_documents(
#                 texts=[comment_text],
#                 metadatas=[comment_metadata]
#             )
#             documents_to_upsert.extend(comment_splits)
#             document_ids.extend([comment_identifier] * len(comment_splits))
        
#         # Process trophies
#         if reddit_data.profile.trophies:
#             trophies_identifier = f"reddit_trophies_{reddit_data.userId}"
#             trophies_text = "Reddit Trophies:\n" + "\n".join([
#                 f"Name: {trophy.name}\nDescription: {trophy.description or 'No description'}\nIcon: {trophy.icon}"
#                 for trophy in reddit_data.profile.trophies
#             ])
            
#             trophies_metadata = {
#                 "userId": reddit_data.userId,
#                 "app": reddit_data.app,
#                 "content_type": "trophies",
#                 "last_updated": int(time.time())
#             }
            
#             trophies_splits = text_splitter.create_documents(
#                 texts=[trophies_text],
#                 metadatas=[trophies_metadata]
#             )
#             documents_to_upsert.extend(trophies_splits)
#             document_ids.extend([trophies_identifier] * len(trophies_splits))
        
#         # Upsert all documents
#         if documents_to_upsert:
#             vector_store.add_documents(documents_to_upsert, ids=document_ids)
        
#         return JSONResponse(
#             content={
#                 "message": f"Successfully upserted Reddit data for user {reddit_data.profile.name}",
#                 "profile_updated": True,
#                 "posts_processed": len(reddit_data.profile.posts),
#                 "comments_processed": len(reddit_data.profile.comments),
#                 "trophies_processed": len(reddit_data.profile.trophies),
#                 "total_chunks": len(documents_to_upsert)
#             },
#             status_code=200
#         )
    
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @app.post("/add-spotify-data")
# async def add_spotify_data(spotify_data: SpotifyData):
#     """
#     Add Spotify user data to the vector database using upsert
#     """
#     try:
#         # Process user profile
#         user_identifier = f"spotify_profile_{spotify_data.userId}"
#         user_text = f"""
#         Spotify Profile:
#         Country: {spotify_data.profile.country}
#         Display Name: {spotify_data.profile.displayName}
#         Email: {spotify_data.profile.email}
#         Profile: {spotify_data.profile.profile}
#         """
        
#         # Create metadata for user profile
#         user_metadata = {
#             "userId": spotify_data.userId,
#             "app": spotify_data.app,
#             "content_type": "profile",
#             "platform_user_id": spotify_data.profile.displayName,
#             "last_updated": int(time.time())
#         }
        
#         # Initialize documents and IDs lists
#         documents_to_upsert = []
#         document_ids = []
        
#         # Split and store user content
#         text_splitter = RecursiveCharacterTextSplitter(
#             chunk_size=5000,
#             chunk_overlap=200
#         )
        
#         # Process user profile
#         user_splits = text_splitter.create_documents(
#             texts=[user_text],
#             metadatas=[user_metadata]
#         )
#         documents_to_upsert.extend(user_splits)
#         document_ids.extend([user_identifier] * len(user_splits))
        
#         # Process top artists
#         for artist in spotify_data.profile.topArtists:
#             artist_identifier = f"spotify_artist_{spotify_data.userId}_{artist.id}"
#             artist_text = f"""
#             Spotify Artist:
#             Name: {artist.name}
#             Followers: {artist.followers}
#             Genres: {', '.join(artist.genres)}
#             Popularity: {artist.popularity}
#             Type: {artist.type}
#             URL: {artist.url}
#             """
            
#             artist_metadata = {
#                 "userId": spotify_data.userId,
#                 "app": spotify_data.app,
#                 "content_type": "artist",
#                 "artist_id": artist.id,
#                 "last_updated": int(time.time())
#             }
            
#             artist_splits = text_splitter.create_documents(
#                 texts=[artist_text],
#                 metadatas=[artist_metadata]
#             )
#             documents_to_upsert.extend(artist_splits)
#             document_ids.extend([artist_identifier] * len(artist_splits))
        
#         # Process playlists
#         for playlist in spotify_data.profile.playlists:
#             playlist_identifier = f"spotify_playlist_{spotify_data.userId}_{playlist.id}"
#             playlist_text = f"""
#             Spotify Playlist:
#             Name: {playlist.name}
#             Description: {playlist.description}
#             URL: {playlist.url}
#             """
            
#             playlist_metadata = {
#                 "userId": spotify_data.userId,
#                 "app": spotify_data.app,
#                 "content_type": "playlist",
#                 "playlist_id": playlist.id,
#                 "last_updated": int(time.time())
#             }
            
#             playlist_splits = text_splitter.create_documents(
#                 texts=[playlist_text],
#                 metadatas=[playlist_metadata]
#             )
#             documents_to_upsert.extend(playlist_splits)
#             document_ids.extend([playlist_identifier] * len(playlist_splits))
        
#         # Process following
#         for following in spotify_data.profile.following:
#             following_identifier = f"spotify_following_{spotify_data.userId}_{following.id}"
#             following_text = f"""
#             Spotify Following:
#             Name: {following.name}
#             Followers: {following.followers}
#             Genres: {', '.join(following.genres)}
#             Popularity: {following.popularity}
#             Type: {following.type}
#             URL: {following.url}
#             """
            
#             following_metadata = {
#                 "userId": spotify_data.userId,
#                 "app": spotify_data.app,
#                 "content_type": "following",
#                 "following_id": following.id,
#                 "last_updated": int(time.time())
#             }
            
#             following_splits = text_splitter.create_documents(
#                 texts=[following_text],
#                 metadatas=[following_metadata]
#             )
#             documents_to_upsert.extend(following_splits)
#             document_ids.extend([following_identifier] * len(following_splits))
        
#         # Process saved shows
#         for show in spotify_data.profile.savedShows:
#             show_identifier = f"spotify_saved_show_{spotify_data.userId}_{show.id}"
#             show_text = f"""
#             Spotify Saved Show:
#             Name: {show.name}
#             Description: {show.description}
#             Added At: {show.added_at}
#             Publisher: {show.publisher}
#             Type: {show.type}
#             Languages: {', '.join(show.languages)}
#             URL: {show.url}
#             """
            
#             show_metadata = {
#                 "userId": spotify_data.userId,
#                 "app": spotify_data.app,
#                 "content_type": "saved_show",
#                 "show_id": show.id,
#                 "last_updated": int(time.time())
#             }
            
#             show_splits = text_splitter.create_documents(
#                 texts=[show_text],
#                 metadatas=[show_metadata]
#             )
#             documents_to_upsert.extend(show_splits)
#             document_ids.extend([show_identifier] * len(show_splits))
        
#         # Process audiobooks
#         for audiobook in spotify_data.profile.audiobooks:
#             audiobook_identifier = f"spotify_audiobook_{spotify_data.userId}_{audiobook.id}"
#             audiobook_text = f"""
#             Spotify Audiobook:
#             Name: {audiobook.name}
#             Description: {audiobook.description}
#             Authors: {', '.join(audiobook.authors)}
#             Available Markets: {', '.join(audiobook.available_markets)}
#             Publisher: {audiobook.publisher}
#             Type: {audiobook.type}
#             Languages: {', '.join(audiobook.languages)}
#             """
            
#             audiobook_metadata = {
#                 "userId": spotify_data.userId,
#                 "app": spotify_data.app,
#                 "content_type": "audiobook",
#                 "audiobook_id": audiobook.id,
#                 "last_updated": int(time.time())
#             }
            
#             audiobook_splits = text_splitter.create_documents(
#                 texts=[audiobook_text],
#                 metadatas=[audiobook_metadata]
#             )
#             documents_to_upsert.extend(audiobook_splits)
#             document_ids.extend([audiobook_identifier] * len(audiobook_splits))
        
#         # Upsert all documents
#         if documents_to_upsert:
#             vector_store.add_documents(documents_to_upsert, ids=document_ids)
        
#         return JSONResponse(
#             content={
#                 "message": f"Successfully upserted Spotify data for user {spotify_data.profile.displayName}",
#                 "profile_updated": True,
#                 "top_artists_processed": len(spotify_data.profile.topArtists),
#                 "playlists_processed": len(spotify_data.profile.playlists),
#                 "following_processed": len(spotify_data.profile.following),
#                 "saved_shows_processed": len(spotify_data.profile.savedShows),
#                 "audiobooks_processed": len(spotify_data.profile.audiobooks),
#                 "total_chunks": len(documents_to_upsert)
#             },
#             status_code=200
#         )
    
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @app.post("/add-github-data")
# async def add_github_data(github_data: GitHubData):
#     """
#     Add GitHub user data to the vector database using upsert
#     """
#     try:
#         # Process user profile
#         user_identifier = f"github_profile_{github_data.userId}"
#         user_text = f"""
#         GitHub Profile:
#         Username: {github_data.profile.name}
#         Login: {github_data.profile.login}
#         Avatar: {github_data.profile.avatar}
#         Email: {github_data.profile.email}
#         Bio: {github_data.profile.bio}
#         Location: {github_data.profile.location}
#         Followers: {github_data.profile.followers}
#         Following: {github_data.profile.following}
#         Public Repos: {github_data.profile.publicRepos}
#         Public Gists: {github_data.profile.publicGists}
#         Account Created: {github_data.profile.createdAt}
#         Last Updated: {github_data.profile.updatedAt}
#         """
        
#         # Create metadata for user profile
#         user_metadata = {
#             "userId": github_data.userId,
#             "app": github_data.app,
#             "content_type": "profile",
#             "platform_user_id": github_data.profile.name,
#             "last_updated": int(time.time())
#         }
        
#         # Initialize documents and IDs lists
#         documents_to_upsert = []
#         document_ids = []
        
#         # Split and store user content
#         text_splitter = RecursiveCharacterTextSplitter(
#             chunk_size=5000,
#             chunk_overlap=200
#         )
        
#         # Process user profile
#         user_splits = text_splitter.create_documents(
#             texts=[user_text],
#             metadatas=[user_metadata]
#         )
#         documents_to_upsert.extend(user_splits)
#         document_ids.extend([user_identifier] * len(user_splits))
        
#         # Process repositories
#         for repo in github_data.profile.repositories:
#             repo_identifier = f"github_repo_{github_data.userId}_{repo.id}"
#             repo_text = f"""
#             GitHub Repository:
#             Name: {repo.name}
#             Description: {repo.description or 'No description'}
#             Language: {repo.language or 'Not specified'}
#             Topics: {', '.join(repo.topics)}
#             Stargazers: {repo.stargazers_count}
#             """
            
#             repo_metadata = {
#                 "userId": github_data.userId,
#                 "app": github_data.app,
#                 "content_type": "repository",
#                 "repo_id": repo.id,
#                 "last_updated": int(time.time())
#             }
            
#             repo_splits = text_splitter.create_documents(
#                 texts=[repo_text],
#                 metadatas=[repo_metadata]
#             )
#             documents_to_upsert.extend(repo_splits)
#             document_ids.extend([repo_identifier] * len(repo_splits))
        
#         # Upsert all documents
#         if documents_to_upsert:
#             vector_store.add_documents(documents_to_upsert, ids=document_ids)
        
#         return JSONResponse(
#             content={
#                 "message": f"Successfully upserted GitHub data for user {github_data.profile.name}",
#                 "profile_updated": True,
#                 "repositories_processed": len(github_data.profile.repositories),
#                 "total_chunks": len(documents_to_upsert)
#             },
#             status_code=200
#         )
    
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))




@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {
        "status": "healthy",
        "service": "context-service",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 