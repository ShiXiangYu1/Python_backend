#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
基础服务模块

提供通用的CRUD（创建、读取、更新、删除）操作基类，
供其他服务继承使用，减少代码重复。
"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base_class import BaseModel as DBBaseModel


# 定义泛型类型变量
ModelType = TypeVar("ModelType", bound=DBBaseModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    基础CRUD操作类
    
    提供通用的数据库操作方法，如创建、读取、更新、删除等。
    使用泛型支持不同模型类型的操作。
    """
    
    def __init__(self, model: Type[ModelType]):
        """
        初始化CRUD服务
        
        设置操作的模型类型。
        
        参数:
            model: 模型类，如User、Model等
        """
        self.model = model
    
    async def get(self, db: AsyncSession, id: Any) -> Optional[ModelType]:
        """
        通过ID获取单个对象
        
        根据主键ID查询单个记录。
        
        参数:
            db: 数据库会话
            id: 对象ID
            
        返回:
            Optional[ModelType]: 查询到的对象，如果不存在则返回None
        """
        query = select(self.model).where(self.model.id == id)
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_multi(
        self, 
        db: AsyncSession, 
        *, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[ModelType]:
        """
        获取多个对象
        
        查询多条记录，支持分页。
        
        参数:
            db: 数据库会话
            skip: 跳过的记录数
            limit: 返回的最大记录数
            
        返回:
            List[ModelType]: 对象列表
        """
        query = select(self.model).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
    
    async def create(self, db: AsyncSession, *, obj_in: CreateSchemaType) -> ModelType:
        """
        创建对象
        
        创建新记录并保存到数据库。
        
        参数:
            db: 数据库会话
            obj_in: 创建对象的数据
            
        返回:
            ModelType: 创建的对象
        """
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """
        更新对象
        
        更新数据库中的记录。
        
        参数:
            db: 数据库会话
            db_obj: 要更新的数据库对象
            obj_in: 更新的数据，可以是Pydantic模型或字典
            
        返回:
            ModelType: 更新后的对象
        """
        obj_data = jsonable_encoder(db_obj)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def remove(self, db: AsyncSession, *, id: Any) -> Optional[ModelType]:
        """
        删除对象
        
        从数据库中删除记录。
        
        参数:
            db: 数据库会话
            id: 对象ID
            
        返回:
            Optional[ModelType]: 删除的对象，如果对象不存在则返回None
        """
        obj = await self.get(db, id)
        if obj:
            await db.delete(obj)
            await db.commit()
        return obj
    
    async def count(self, db: AsyncSession) -> int:
        """
        计算对象总数
        
        获取数据库中该类型对象的总数。
        
        参数:
            db: 数据库会话
            
        返回:
            int: 对象总数
        """
        query = select(func.count()).select_from(self.model)
        result = await db.execute(query)
        return result.scalar_one() 