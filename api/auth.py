from __future__ import annotations

import os

from fastapi import Header, HTTPException, status


def verify_internal_api_key(authorization: str | None = Header(default=None)) -> None:
    """
    内部API向けの Bearer Token 認証。
    環境変数 INTERNAL_API_KEY が設定されていない場合は全リクエストを拒否する。
    Authorization: Bearer <key> ヘッダーを検証する。
    """
    secret_key = os.environ.get("INTERNAL_API_KEY")

    # INTERNAL_API_KEY未設定時は全リクエストを拒否（セキュアデフォルト）
    if not secret_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="INTERNAL_API_KEY is not configured",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if authorization is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header is required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    parts = authorization.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header must be Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = parts[1]
    if token != secret_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
