#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Web路由处理模块

此模块定义了Web前端的所有路由，负责页面的渲染和响应。
包含首页、登录、注册、模型管理等页面的路由处理。
"""

import os
from pathlib import Path
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

# 创建路由
web_router = APIRouter()

# 设置模板目录
templates_path = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_path))


@web_router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """
    渲染首页
    
    参数:
        request: 请求对象
        
    返回:
        HTMLResponse: 渲染后的HTML页面
    """
    return templates.TemplateResponse(
        "index.html", 
        {"request": request, "title": "AI模型管理平台"}
    )


@web_router.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    """
    渲染登录页面或重定向到静态HTML登录页
    
    参数:
        request: 请求对象
        
    返回:
        HTMLResponse或RedirectResponse: 渲染后的HTML页面或重定向响应
    """
    # 重定向到静态HTML登录页
    return RedirectResponse(url="/static/html/login.html")
    
    # 以下代码注释掉，不再使用模板渲染
    # return templates.TemplateResponse(
    #     "login.html", 
    #     {"request": request, "title": "登录"}
    # )


@web_router.get("/register", response_class=HTMLResponse)
async def register(request: Request):
    """
    渲染注册页面或重定向到静态HTML注册页
    
    参数:
        request: 请求对象
        
    返回:
        HTMLResponse或RedirectResponse: 渲染后的HTML页面或重定向响应
    """
    # 重定向到静态HTML注册页
    return RedirectResponse(url="/static/html/register.html")
    
    # 以下代码注释掉，不再使用模板渲染
    # return templates.TemplateResponse(
    #     "register.html", 
    #     {"request": request, "title": "注册"}
    # )


@web_router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """
    渲染仪表盘页面
    
    参数:
        request: 请求对象
        
    返回:
        HTMLResponse: 渲染后的HTML页面
    """
    return templates.TemplateResponse(
        "dashboard.html", 
        {"request": request, "title": "仪表盘"}
    )


@web_router.get("/models", response_class=HTMLResponse)
async def models(request: Request):
    """
    渲染模型管理页面
    
    参数:
        request: 请求对象
        
    返回:
        HTMLResponse: 渲染后的HTML页面
    """
    return templates.TemplateResponse(
        "models.html", 
        {"request": request, "title": "模型管理"}
    )


@web_router.get("/api-keys", response_class=HTMLResponse)
async def api_keys(request: Request):
    """
    渲染API密钥管理页面
    
    参数:
        request: 请求对象
        
    返回:
        HTMLResponse: 渲染后的HTML页面
    """
    return templates.TemplateResponse(
        "api_keys.html", 
        {"request": request, "title": "API密钥管理"}
    )


@web_router.get("/profile", response_class=HTMLResponse)
async def profile(request: Request):
    """
    渲染用户资料页面
    
    参数:
        request: 请求对象
        
    返回:
        HTMLResponse: 渲染后的HTML页面
    """
    return templates.TemplateResponse(
        "profile.html", 
        {"request": request, "title": "个人资料"}
    ) 