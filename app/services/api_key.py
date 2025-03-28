#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
API密钥服务模块

提供API密钥相关的业务逻辑实现，如创建、验证和撤销API密钥等。
为API访问提供安全的认证机制。
"""

from datetime import datetime
from typing import List, Optional, Union, Dict, Any, Tuple

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.api_key import APIKey
from app.models.user import User
from app.schemas.api_key import APIKeyCreate, APIKeyUpdate
from app.services.base import CRUDBase


class APIKeyService(CRUDBase[APIKey, APIKeyCreate, APIKeyUpdate]):
    """
    API密钥服务类
    
    继承自基础CRUD服务类，提供API密钥特定的业务逻辑。
    如验证密钥有效性、更新使用情况等。
    """
    
    async def create_with_user(
        self, db: AsyncSession, *, obj_in: APIKeyCreate, user_id: str
    ) -> APIKey:
        """
        为用户创建API密钥
        
        创建与特定用户关联的API密钥。
        
        参数:
            db: 数据库会话
            obj_in: API密钥创建数据
            user_id: 用户ID
            
        返回:
            APIKey: 创建的API密钥对象
        """
        db_obj = APIKey(
            name=obj_in.name,
            scopes=obj_in.scopes,
            is_active=obj_in.is_active,
            expires_at=obj_in.expires_at,
            user_id=user_id
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def get_multi_by_user(
        self, db: AsyncSession, *, user_id: str, skip: int = 0, limit: int = 100
    ) -> List[APIKey]:
        """
        获取用户的API密钥列表
        
        查询特定用户的API密钥列表，支持分页。
        
        参数:
            db: 数据库会话
            user_id: 用户ID
            skip: 跳过的记录数
            limit: 返回的最大记录数
            
        返回:
            List[APIKey]: API密钥列表
        """
        query = select(APIKey).where(APIKey.user_id == user_id).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_by_key(self, db: AsyncSession, *, key: str) -> Optional[APIKey]:
        """
        通过密钥值获取API密钥
        
        根据密钥值查询API密钥记录。
        
        参数:
            db: 数据库会话
            key: 密钥值
            
        返回:
            Optional[APIKey]: 查询到的API密钥，如果不存在则返回None
        """
        query = select(APIKey).where(APIKey.key == key)
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def verify_key(self, db: AsyncSession, *, key: str) -> Optional[APIKey]:
        """
        验证API密钥
        
        验证API密钥是否有效，包括检查是否激活、是否过期等。
        同时更新使用统计信息。
        
        参数:
            db: 数据库会话
            key: 密钥值
            
        返回:
            Optional[APIKey]: 有效的API密钥，如果无效则返回None
        """
        api_key = await self.get_by_key(db, key=key)
        if not api_key:
            return None
        
        # 检查密钥是否有效
        if not api_key.is_valid:
            return None
        
        # 更新使用统计
        api_key.update_usage()
        db.add(api_key)
        await db.commit()
        await db.refresh(api_key)
        
        return api_key
    
    async def count_by_user(self, db: AsyncSession, *, user_id: str) -> int:
        """
        计算用户的API密钥数量
        
        获取特定用户的API密钥总数。
        
        参数:
            db: 数据库会话
            user_id: 用户ID
            
        返回:
            int: API密钥总数
        """
        query = select(func.count()).select_from(APIKey).where(APIKey.user_id == user_id)
        result = await db.execute(query)
        return result.scalar_one()
    
    async def get_api_keys_with_pagination(
        self, db: AsyncSession, *, user_id: str, skip: int = 0, limit: int = 100
    ) -> Tuple[List[APIKey], int]:
        """
        获取分页API密钥列表
        
        查询特定用户的API密钥列表，支持分页，并返回总数。
        
        参数:
            db: 数据库会话
            user_id: 用户ID
            skip: 跳过的记录数
            limit: 返回的最大记录数
            
        返回:
            Tuple[List[APIKey], int]: API密钥列表和总数
        """
        query = select(APIKey).where(APIKey.user_id == user_id).offset(skip).limit(limit)
        result = await db.execute(query)
        api_keys = result.scalars().all()
        
        count = await self.count_by_user(db, user_id=user_id)
        
        return api_keys, count
    
    async def deactivate(self, db: AsyncSession, *, id: str) -> Optional[APIKey]:
        """
        停用API密钥
        
        将API密钥状态设置为非激活。
        
        参数:
            db: 数据库会话
            id: API密钥ID
            
        返回:
            Optional[APIKey]: 更新后的API密钥，如果不存在则返回None
        """
        api_key = await self.get(db, id)
        if not api_key:
            return None
        
        api_key.is_active = False
        db.add(api_key)
        await db.commit()
        await db.refresh(api_key)
        
        return api_key


# 创建API密钥服务单例
api_key_service = APIKeyService(APIKey)