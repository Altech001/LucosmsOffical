from fastapi import APIRouter, Depends, Request, HTTPException
from clerk_backend_api import Clerk
from clerk_backend_api.models import ClerkErrors, SDKError
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from database import get_db
import models
import schemas
import jwt

load_dotenv()

# Clerk secret key for backend authentication
CLERK_SECRET_KEY = os.getenv('CLERK_SECRET_KEY')

# Initialize FastAPI application
auth_router = APIRouter()


# Initialize Clerk client with the secret key
clerk_client = Clerk(bearer_auth=CLERK_SECRET_KEY)

# Dependency function to get the current authenticated user
async def get_current_user(request: Request, db: Session = Depends(get_db)):
    # Get the session token from the Authorization header
    auth_header = request.headers.get('Authorization', '')
    print(80*'-')
    print(f"Raw Authorization header: {auth_header}")
    print(80*'-')
    
    # Check if the Authorization header exists
    if not auth_header:
        raise HTTPException(status_code=401, detail='Authorization header missing')
    
    # Expected format: 'Bearer <session_token>'
    if not auth_header.startswith('Bearer '):
        print("Invalid authorization header format. Expected 'Bearer <session_token>'")
        raise HTTPException(status_code=401, detail='Invalid authorization header format')
    
    session_token = auth_header.replace('Bearer ', '')
    print(f"Session token: {session_token}")
    
    try:
        # Verify the session token with Clerk using the client API
        try:
            # First approach - try to get session directly with the token
            session = clerk_client.sessions.get_session(session_token)
            print(f"Session retrieved: {session}")
        except Exception as session_error:
            print(f"Direct session retrieval failed: {str(session_error)}")
            
            try:
                # Alternative approach - decode the JWT manually
                decoded_token = jwt.decode(session_token, options={"verify_signature": False})
                print(f"Decoded token: {decoded_token}")
                
                # Extract session ID from the decoded token
                session_id = decoded_token.get('sid')
                if not session_id:
                    raise HTTPException(status_code=401, detail='Invalid session token: No session ID found')
                
                print(f"Extracted session ID: {session_id}")
                
                # Get detailed session info using the session ID
                session = clerk_client.sessions.get(session_id=session_id)
            except Exception as jwt_error:
                print(f"JWT decoding failed: {str(jwt_error)}")
                raise HTTPException(status_code=401, detail='Failed to validate session token')
        
        # Fetch user details from Clerk
        user_details = clerk_client.users.get(user_id=session.user_id)
        email = user_details.email_addresses[0].email_address if user_details.email_addresses else None
        username = user_details.username or user_details.first_name or f"user_{session.user_id}"

        # Check if user exists in the database
        db_user = db.query(models.Users).filter(models.Users.email == email).first()
        if not db_user:
            # Automatically add user to the database
            new_user = models.Users(
                username=username,  # Use 'userid' to match your model
                email=email,
                clerk_user_id=session.user_id  # Optional: Include if your model supports it
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            print(f"New user added to database: {email}")
        else:
            print(f"User already exists in database: {email}")
        
        # Return the session object
        return session
    
    except ClerkErrors as e:
        # Handle Clerk-specific errors
        print(f"Clerk error: {str(e)}")
        raise HTTPException(status_code=401, detail=f'Invalid or expired session token: {str(e)}')
    except SDKError as e:
        # Handle general SDK errors
        print(f"SDK error: {str(e)}")
        raise HTTPException(status_code=500, detail=f'Internal server error: {str(e)}')
    except Exception as e:
        # Handle unexpected errors
        print(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f'Server error: {str(e)}')

# Protected route that requires authentication
@auth_router.get("/protected")
async def protected_route(user=Depends(get_current_user)):
    try:
        # Retrieve detailed user information from Clerk
        user_details = clerk_client.users.get(user_id=user.user_id)
        print(f"User details retrieved: {user_details.first_name} {user_details.last_name}")
        
        # Return a personalized message using the user's first name
        return {
            "message": f"Hello, {user_details.first_name}!",
            "user_id": user_details.id,
            "session": user_details.profile_image_url,
            "email": user_details.email_addresses[0].email_address if user_details.email_addresses else None,
        }
    except Exception as e:
        print(f"Error in protected route: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching user details: {str(e)}")
