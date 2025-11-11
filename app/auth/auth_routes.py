from . import auth_bp
from .services import register_user, login_user, logout_user_by_jti, store_refresh_token, verify_email_token
from .validators import validate_signup_data, validate_login_data
from .models import User
from flask import request, jsonify
from flask_jwt_extended import (
    jwt_required, 
    get_jwt_identity, 
    create_access_token,
    create_refresh_token,
    set_refresh_cookies,
    unset_jwt_cookies,
    get_jti,
    get_jwt
)
import json

# -------------------- SIGNUP --------------------
@auth_bp.route('/signup', methods=['POST'])
def signup():
    try:
        data = request.get_json()
        validated_data = validate_signup_data(data)

        new_user = register_user(
            email=validated_data.get("email"),
            password=validated_data.get("password")
        )

        return jsonify({
            "message": "User created successfully",
            "User": {"id": new_user.id, "email": new_user.email}
        }), 201
    
    except ValueError as e:
        return jsonify({"error": str(e)}), 422
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# -------------------- LOGIN --------------------
@auth_bp.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json()
        validated_data = validate_login_data(data)

        user = login_user(
            email=validated_data.get('email'),
            password=validated_data.get('password')
        )

        access_token = create_access_token(
            identity=str(user.id),
            additional_claims={
                "role": user.role,
                "is_email_verified": user.is_email_verified
            }
        )
        refresh_token = create_refresh_token(identity=str(user.id))

        # Store refresh JTI in DB
        jti = get_jti(refresh_token)
        store_refresh_token(jti, user.id)

        response = jsonify(access_token=access_token)

        # ✅ Set persistent cross-site cookie
        set_refresh_cookies(response, refresh_token,max_age=7 * 24 * 60 * 60)
        return response, 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 401

# --- REFRESH (Dramatically Simplified) ---
@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True) # <-- This decorator does all the work!
def refresh():
    # 1. The @jwt_required decorator and our 'check_if_token_is_revoked'
    #    callback have already done all the work:
    #    - Verified the cookie.
    #    - Verified the CSRF token.
    #    - Verified the token's 'jti' IS in our database.

    # 2. We just create and return a new access token.
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user: return jsonify({"error": "User not found"}), 404
        
    new_access_token = create_access_token(
        identity=str(user.id),
        additional_claims={
            "role": user.role,
            "is_email_verified": user.is_email_verified
        }
    )
    return jsonify(access_token=new_access_token), 200
    
# --- LOGOUT (Dramatically Simplified) ---
@auth_bp.route('/logout', methods=['DELETE'])
@jwt_required(refresh=True)
def logout():
    try:
        # 1. The decorator has already verified the cookie is valid.
        # 2. We just get its JTI and revoke it.
        jti = get_jwt()['jti']
        logout_user_by_jti(jti)
        
        # 3. Create a response and tell the user's browser
        #    to delete the refresh/CSRF cookies.
        response = jsonify(message="Logout successful. Token revoked.")
        unset_jwt_cookies(response)
        return response, 200
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 401

# -------------------- EMAIL VERIFY --------------------
@auth_bp.route('/verify-email', methods=['GET'])
def verify_email():
    token = request.args.get('token')

    try:
        user = verify_email_token(token)
        return jsonify(message=f"Email for {user.email} successfully verified!"), 200
    
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@auth_bp.route('/user/profile', methods=['GET'])
@jwt_required()
def user_profile():
    user_id = get_jwt_identity()
    from app.auth.models import User
    from app.RAG import r  # redis
    
    user = User.query.get(user_id)
    cache = r.get(f"lex:user:{user_id}")
    cache_data = json.loads(cache) if cache else {}
    
    return jsonify({
        "email": user.email,
        "documents": 1 if cache_data.get("analysis_result") else 0,
        "chats": len(cache_data.get("chat_history", [])),
        "last_active": cache_data.get("timestamp")
    })
