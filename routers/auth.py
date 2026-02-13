"""
Authentication router - GOOGLE SIGN-IN ONLY
Simple Gmail account authentication
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from models.schemas import GoogleSignInRequest, AuthResponse
from config.firebase_init import verify_firebase_token, get_user, create_user, update_last_login
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Dependency to get current authenticated user from Bearer token."""
    try:
        token = credentials.credentials
        decoded_token = verify_firebase_token(token)
        return decoded_token
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(status_code=401, detail="Invalid authentication token")


@router.post("/login", response_model=AuthResponse)
async def google_login(request: GoogleSignInRequest):
    """
    Google Sign-In — Single authentication endpoint.

    Flutter flow:
    1. User clicks "Sign in with Google"
    2. Google Sign-In popup appears
    3. User selects Gmail account
    4. Flutter gets Firebase token
    5. Send token to this endpoint
    6. Done! User is authenticated
    """
    try:
        if not request.firebase_token or not request.firebase_token.strip():
            raise HTTPException(status_code=422, detail="firebase_token is required")

        # Verify Firebase token
        decoded_token = verify_firebase_token(request.firebase_token)

        user_id = decoded_token["uid"]
        email = decoded_token.get("email", "")
        display_name = decoded_token.get("name", "")
        photo_url = decoded_token.get("picture", "")
        provider = decoded_token.get("firebase", {}).get("sign_in_provider", "")

        # Ensure it's Google sign-in
        if provider and provider != "google.com":
            raise HTTPException(
                status_code=400,
                detail="Only Google Sign-In is supported. Please use your Gmail account.",
            )

        logger.info(f"Google sign-in: {email}")

        # Check if user exists
        user = await get_user(user_id)

        if not user:
            # New user — create profile
            user = await create_user(
                user_id=user_id,
                email=email,
                display_name=display_name,
                photo_url=photo_url,
                provider=provider or "google.com",
            )
            logger.info(f"✅ New user created: {email}")
        else:
            # Existing user — update last login
            await update_last_login(user_id)
            logger.info(f"✅ User logged in: {email}")

        return AuthResponse(
            access_token=request.firebase_token,
            token_type="bearer",
            user_id=user_id,
            email=email,
            display_name=display_name,
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Google sign-in error: {e}")
        raise HTTPException(status_code=500, detail="Google sign-in failed")


@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """
    Logout — Clear session.

    Client should:
    1. Call this endpoint (optional, for analytics)
    2. Sign out from Google: GoogleSignIn().signOut()
    3. Sign out from Firebase: FirebaseAuth.instance.signOut()
    4. Clear stored token
    """
    try:
        email = current_user.get("email", "")
        logger.info(f"User logged out: {email}")
        return {"status": "success", "message": "Logged out successfully"}
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(status_code=500, detail="Logout failed")


@router.get("/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    Get current user info.
    Returns profile information from both Firebase and Firestore.
    """
    try:
        user_id = current_user["uid"]
        user = await get_user(user_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return {
            "user_id": user_id,
            "email": current_user.get("email", ""),
            "display_name": user.get("displayName", ""),
            "photo_url": user.get("photoUrl", ""),
            "email_verified": current_user.get("email_verified", False),
            "created_at": user.get("createdAt"),
            "last_login": user.get("lastLogin"),
            "onboarding_complete": user.get("onboardingComplete", False),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user info error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user info")
