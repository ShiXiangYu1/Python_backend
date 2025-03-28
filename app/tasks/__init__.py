#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
任务包初始化

用于Celery任务的包初始化，导入所有任务模块，使它们对Celery可见。
"""

from app.tasks import common_tasks, model_tasks, high_priority_tasks 