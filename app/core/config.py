#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
应用配置模块

该模块负责加载和管理应用的配置参数，包括环境变量、数据库连接信息、
JWT设置等。通过pydantic_settings提供类型安全的配置访问。
"""

import os
import secrets
from typing import List, Union, Optional, Dict, Any
from pydantic import field_validator, AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    应用程序设置类

    使用pydantic_settings管理应用程序配置，支持从环境变量、.env文件等加载配置。
    提供类型检查和默认值设置，确保配置的可靠性和正确性。
    """

    # 基本设置
    APP_NAME: str = "AI模型管理与服务平台"
    PROJECT_NAME: str = "AI模型管理与服务平台"
    PROJECT_VERSION: str = "0.1.0"
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    APP_PORT: int = 8000
    APP_HOST: str = "0.0.0.0"
    SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    API_PREFIX: str = "/api"

    # 数据库设置
    DB_CONNECTION: str = "mysql"
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_DATABASE: str = "ai_model_platform"
    DB_USERNAME: str = "root"
    DB_PASSWORD: str = ""
    DATABASE_URL: Optional[str] = None

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """
        生成SQLAlchemy数据库连接URI

        基于配置的数据库参数，生成标准的SQLAlchemy连接字符串。
        支持MySQL和SQLite等不同数据库后端。

        返回:
            str: SQLAlchemy兼容的数据库连接字符串
        """
        if self.DATABASE_URL:
            return self.DATABASE_URL

        if self.DB_CONNECTION == "sqlite":
            return f"sqlite:///{self.DB_DATABASE}.db"
        return f"{self.DB_CONNECTION}+pymysql://{self.DB_USERNAME}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_DATABASE}"

    # Redis设置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0

    @property
    def REDIS_URI(self) -> str:
        """
        生成Redis连接URI

        基于配置的Redis参数，生成标准的Redis连接字符串。

        返回:
            str: Redis连接字符串
        """
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        
    @property
    def REDIS_URL(self) -> str:
        """
        生成Redis连接URL，与REDIS_URI保持一致

        为了兼容使用REDIS_URL的缓存系统，提供与REDIS_URI相同的连接字符串。

        返回:
            str: Redis连接字符串
        """
        return self.REDIS_URI

    # Elasticsearch设置
    ES_HOST: str = "localhost"
    ES_PORT: int = 9200
    ES_USERNAME: Optional[str] = None
    ES_PASSWORD: Optional[str] = None

    @property
    def ES_URI(self) -> str:
        """
        生成Elasticsearch连接URI

        基于配置的Elasticsearch参数，生成Elasticsearch连接字符串。

        返回:
            str: Elasticsearch连接字符串
        """
        if self.ES_USERNAME and self.ES_PASSWORD:
            return f"http://{self.ES_USERNAME}:{self.ES_PASSWORD}@{self.ES_HOST}:{self.ES_PORT}"
        return f"http://{self.ES_HOST}:{self.ES_PORT}"

    # JWT设置
    JWT_SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    JWT_ALGORITHM: str = "HS256"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    API_KEY_HEADER: str = "X-API-Key"

    # 模型设置
    MODEL_UPLOAD_DIR: str = "./model_uploads"
    MAX_MODEL_SIZE: int = 1073741824  # 1GB

    # 日志设置
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "./logs"

    # CORS设置
    CORS_ALLOW_ORIGINS: str = "http://localhost:3000,http://localhost:8000"
    CORS_ORIGINS: Optional[Union[List[str], str]] = None

    @field_validator("CORS_ALLOW_ORIGINS")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        """
        验证并格式化CORS允许的源

        将字符串格式的CORS配置转换为列表格式，方便应用使用。

        参数:
            v: 原始的CORS配置值，可以是字符串或列表

        返回:
            Union[List[str], str]: 格式化后的CORS配置值
        """
        if isinstance(v, str) and not v.startswith("["):
            return [origin.strip() for origin in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # 线程池设置
    WORKER_POOL_SIZE: int = 4

    # Pydantic设置
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow",
    )


# 实例化设置对象，导出为模块级变量
settings = Settings()
