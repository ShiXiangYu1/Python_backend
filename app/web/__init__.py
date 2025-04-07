#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Web前端路由模块

此模块负责处理Web前端页面的路由和渲染。
作为应用的前端入口点，它提供用户界面并与API进行交互。
"""

from fastapi import APIRouter
from app.web.routes import web_router

__all__ = ["web_router"]
