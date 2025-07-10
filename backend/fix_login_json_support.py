#!/usr/bin/env python3
"""
Add JSON login support to the main application.
This script patches the auth.py file to support both form data and JSON login.
"""

import os
import sys

# The additional imports needed
additional_imports = """from typing import Union
from pydantic import BaseModel

class JsonLoginRequest(BaseModel):
    email: str
    password: str
"""

# The new login endpoint that supports both formats
new_login_endpoint = '''
@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """
    OAuth2 compatible token login that supports both form data and JSON.
    
    Args:
        request: HTTP request object
        db: Database session
        
    Returns:
        Access and refresh tokens
        
    Raises:
        HTTPException: If credentials are invalid
    """
    # Try to parse as JSON first
    username = None
    password = None
    
    content_type = request.headers.get("content-type", "")
    
    if "application/json" in content_type:
        try:
            body = await request.json()
            username = body.get("email", body.get("username", "")).lower()
            password = body.get("password", "")
        except:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON body"
            )
    elif "application/x-www-form-urlencoded" in content_type:
        try:
            form_data = await request.form()
            username = form_data.get("username", "").lower()
            password = form_data.get("password", "")
        except:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid form data"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Content-Type must be application/json or application/x-www-form-urlencoded"
        )
    
    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Username and password are required"
        )
    
    # Get user by email (username field contains email)
    result = await db.execute(
        select(User).where(User.email == username)
    )
    user = result.scalar_one_or_none()
    
    # Verify user and password
    if not user or not SecurityUtils.verify_password(password, user.password_hash):
        # Log failed attempt
        if user:
            attempt = TwoFAAttempt(
                user_id=user.id,
                attempt_type="login",
                success=False,
                ip_address=request.client.host if request else "unknown",
            )
            db.add(attempt)
            await db.commit()
            
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Check if user is verified
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not verified. Please check your email for verification link."
        )
    
    # Check if 2FA is enabled
    if user.two_factor_enabled and user.two_factor_secret:
        # Return temporary token for 2FA verification
        temp_token = SecurityUtils.create_access_token(
            subject=str(user.id),
            expires_delta=timedelta(minutes=5),
            additional_claims={"temp": True, "purpose": "2fa"}
        )
        
        return TokenResponse(
            access_token=temp_token,
            token_type="bearer",
            expires_in=300,  # 5 minutes
            refresh_token=None,
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    await db.commit()
    
    # Create tokens
    access_token = SecurityUtils.create_access_token(subject=str(user.id))
    refresh_token = SecurityUtils.create_refresh_token(subject=str(user.id))
    
    # Log successful login
    attempt = TwoFAAttempt(
        user_id=user.id,
        attempt_type="login",
        success=True,
        ip_address=request.client.host if request else "unknown",
    )
    db.add(attempt)
    await db.commit()
    
    # Return token response with user info for JSON requests
    response_data = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }
    
    # Add user info for JSON requests (like test server does)
    if "application/json" in content_type:
        response_data["user"] = {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role,
            "is_active": user.is_active,
            "is_verified": user.is_verified
        }
    
    return TokenResponse(**response_data)
'''

def main():
    """Apply the fix to make login work with JSON."""
    auth_file = "api/routes/auth.py"
    
    if not os.path.exists(auth_file):
        print(f"Error: {auth_file} not found. Run this from the backend directory.")
        sys.exit(1)
    
    # Read the current file
    with open(auth_file, 'r') as f:
        content = f.read()
    
    # Check if already patched
    if "application/json" in content and "await request.json()" in content:
        print("✅ File already patched for JSON support!")
        return
    
    # Create backup
    backup_file = auth_file + ".backup"
    with open(backup_file, 'w') as f:
        f.write(content)
    print(f"✅ Created backup: {backup_file}")
    
    # Find the login endpoint and replace it
    import_section_end = content.find("router = APIRouter()")
    if import_section_end == -1:
        print("Error: Could not find router initialization")
        sys.exit(1)
    
    # Add additional imports after the existing imports
    new_content = content[:import_section_end] + additional_imports + "\n\n" + content[import_section_end:]
    
    # Find and replace the login endpoint
    login_start = new_content.find('@router.post("/login"')
    if login_start == -1:
        print("Error: Could not find login endpoint")
        sys.exit(1)
    
    # Find the end of the login function (next @router or end of file)
    login_end = new_content.find("@router", login_start + 1)
    if login_end == -1:
        login_end = len(new_content)
    
    # Replace the login endpoint
    final_content = new_content[:login_start] + new_login_endpoint + "\n\n" + new_content[login_end:]
    
    # Write the updated file
    with open(auth_file, 'w') as f:
        f.write(final_content)
    
    print("✅ Successfully patched auth.py to support JSON login!")
    print("\nThe login endpoint now supports both:")
    print("1. JSON format: {\"email\": \"...\", \"password\": \"...\"}")
    print("2. Form data: username=...&password=...")
    print("\nRestart the server for changes to take effect.")

if __name__ == "__main__":
    main()