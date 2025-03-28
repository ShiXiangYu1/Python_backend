#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
通用Schema模块

定义通用的请求和响应数据模型，如分页参数、消息响应等。
这些Schema可以被多个API端点共享使用。
"""

from typing import Any, Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field
from pydantic.generics import GenericModel


# 通用消息响应
class Message(BaseModel):
    """
    消息响应Schema
    
    用于返回简单的成功或错误消息。
    """
    detail: str = Field(..., description="消息内容")


# 分页查询参数
class PaginationParams(BaseModel):
    """
    分页查询参数Schema
    
    用于接收API请求中的分页参数。
    """
    page: int = Field(1, ge=1, description="页码，从1开始")
    page_size: int = Field(10, ge=1, le=100, description="每页条目数")
    
    
# 排序查询参数
class SortParams(BaseModel):
    """
    排序查询参数Schema
    
    用于接收API请求中的排序参数。
    """
    sort_by: str = Field("created_at", description="排序字段")
    sort_order: str = Field("desc", description="排序方向，asc或desc")


# 定义一个可以用于任何数据类型的数据类型变量
T = TypeVar('T')


# 分页响应
class Page(GenericModel, Generic[T]):
    """
    分页响应Schema
    
    用于返回分页数据，支持任何数据类型的列表。
    """
    items: List[T] = Field(..., description="数据列表")
    total: int = Field(..., description="总条目数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页条目数")
    pages: int = Field(..., description="总页数")
    
    @classmethod
    def create(cls, items: List[T], total: int, page: int, page_size: int) -> "Page[T]":
        """
        创建分页响应
        
        根据数据列表、总条目数和分页参数创建分页响应。
        
        参数:
            items: 数据列表
            total: 总条目数
            page: 当前页码
            page_size: 每页条目数
            
        返回:
            Page[T]: 分页响应对象
        """
        pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages
        )


# HTTP错误响应
class HTTPError(BaseModel):
    """
    HTTP错误响应Schema
    
    用于返回HTTP错误信息。
    """
    detail: str = Field(..., description="错误信息")


# 验证错误响应
class ValidationError(BaseModel):
    """
    验证错误响应Schema
    
    用于返回请求数据验证错误信息。
    """
    detail: List[Dict[str, Any]] = Field(..., description="错误详情列表") 