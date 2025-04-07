#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
用户服务模块

提供用户相关的业务逻辑实现，如用户注册、认证、权限验证等。
与数据库交互并进行相应的业务处理。
"""

from typing import Any, Dict, Optional, Union, List, Tuple

from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_password_hash, verify_password
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.services.base import CRUDBase


class UserService(CRUDBase[User, UserCreate, UserUpdate]):
    """
    用户服务类

    继承自基础CRUD服务类，提供用户特定的业务逻辑。
    如用户认证、密码处理等特殊操作。
    """

    async def get_by_username(
        self, db: AsyncSession, *, username: str
    ) -> Optional[User]:
        """
        通过用户名获取用户

        根据用户名查询用户记录。

        参数:
            db: 数据库会话
            username: 用户名

        返回:
            Optional[User]: 查询到的用户，如果不存在则返回None
        """
        query = select(User).where(User.username == username)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_email(self, db: AsyncSession, *, email: str) -> Optional[User]:
        """
        通过邮箱获取用户

        根据邮箱地址查询用户记录。

        参数:
            db: 数据库会话
            email: 邮箱地址

        返回:
            Optional[User]: 查询到的用户，如果不存在则返回None
        """
        query = select(User).where(User.email == email)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_username_or_email(
        self, db: AsyncSession, *, username_or_email: str
    ) -> Optional[User]:
        """
        通过用户名或邮箱获取用户

        根据用户名或邮箱地址查询用户记录，用于登录验证。

        参数:
            db: 数据库会话
            username_or_email: 用户名或邮箱地址

        返回:
            Optional[User]: 查询到的用户，如果不存在则返回None
        """
        query = select(User).where(
            or_(User.username == username_or_email, User.email == username_or_email)
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def create(self, db: AsyncSession, *, obj_in: UserCreate) -> User:
        """
        创建新用户

        根据提供的数据创建新用户，并对密码进行哈希处理。

        参数:
            db: 数据库会话
            obj_in: 用户创建数据

        返回:
            User: 创建的用户对象
        """
        db_obj = User(
            username=obj_in.username,
            email=obj_in.email,
            hashed_password=create_password_hash(obj_in.password),
            full_name=obj_in.full_name,
            is_active=obj_in.is_active,
            role=obj_in.role,
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: User,
        obj_in: Union[UserUpdate, Dict[str, Any]]
    ) -> User:
        """
        更新用户

        更新用户信息，支持更新密码（需要进行哈希处理）。

        参数:
            db: 数据库会话
            db_obj: 要更新的用户对象
            obj_in: 更新数据

        返回:
            User: 更新后的用户对象
        """
        update_data = (
            obj_in if isinstance(obj_in, dict) else obj_in.dict(exclude_unset=True)
        )

        # 如果更新包含密码，需要哈希处理
        if "password" in update_data and update_data["password"]:
            hashed_password = create_password_hash(update_data["password"])
            del update_data["password"]
            update_data["hashed_password"] = hashed_password

        return await super().update(db, db_obj=db_obj, obj_in=update_data)

    async def authenticate(
        self, db: AsyncSession, *, username_or_email: str, password: str
    ) -> Optional[User]:
        """
        用户认证

        验证用户名/邮箱和密码是否匹配。

        参数:
            db: 数据库会话
            username_or_email: 用户名或邮箱
            password: 密码

        返回:
            Optional[User]: 认证成功的用户，如果认证失败则返回None
        """
        user = await self.get_by_username_or_email(
            db, username_or_email=username_or_email
        )
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    async def is_active(self, user: User) -> bool:
        """
        检查用户是否激活

        参数:
            user: 用户对象

        返回:
            bool: 用户是否激活
        """
        return user.is_active

    async def get_users_with_pagination(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> Tuple[List[User], int]:
        """
        获取分页用户列表

        查询用户列表，支持分页，并返回总数。

        参数:
            db: 数据库会话
            skip: 跳过的记录数
            limit: 返回的最大记录数

        返回:
            Tuple[List[User], int]: 用户列表和总数
        """
        query = select(User).offset(skip).limit(limit)
        result = await db.execute(query)
        users = result.scalars().all()

        count_query = select(func.count()).select_from(User)
        count_result = await db.execute(count_query)
        total = count_result.scalar_one()

        return users, total


# 创建用户服务单例
user_service = UserService(User)
