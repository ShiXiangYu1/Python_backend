/**
 * 模型管理页面JavaScript
 * 
 * 实现模型的列表展示、创建、更新、删除和部署等功能
 */

// 立即执行函数，避免全局变量污染
(function() {
    'use strict';
    
    // 页面加载完成后执行
    document.addEventListener('DOMContentLoaded', function() {
        // 初始化模型列表
        initModelList();
        
        // 设置模型创建表单监听器
        setupModelCreateForm();
        
        // 设置模型操作按钮监听器
        setupModelActions();
        
        // 设置模型搜索功能
        setupModelSearch();
        
        // 设置分页功能
        setupPagination();
    });
    
    /**
     * 初始化模型列表
     * @param {number} page - 页码
     * @param {number} pageSize - 每页数量
     * @param {string} searchQuery - 搜索关键词
     */
    function initModelList(page = 1, pageSize = 10, searchQuery = '') {
        const modelListElement = document.getElementById('modelList');
        const loadingElement = document.getElementById('loadingModels');
        
        if (!modelListElement) return;
        
        // 显示加载状态
        if (loadingElement) loadingElement.style.display = 'flex';
        if (modelListElement) modelListElement.innerHTML = '';
        
        // 构建API请求URL
        let url = `/api/v1/models?page=${page}&page_size=${pageSize}`;
        if (searchQuery) {
            url += `&search=${encodeURIComponent(searchQuery)}`;
        }
        
        // 获取模型列表
        const token = localStorage.getItem('access_token');
        
        fetch(url, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('获取模型列表失败');
            }
            return response.json();
        })
        .then(data => {
            // 更新分页信息
            updatePagination(data.page, data.pages, data.total);
            
            // 隐藏加载状态
            if (loadingElement) loadingElement.style.display = 'none';
            
            // 如果没有模型，显示提示信息
            if (data.items.length === 0) {
                modelListElement.innerHTML = `
                    <tr>
                        <td colspan="6" class="text-center py-4">
                            <div class="alert alert-info mb-0">
                                <i class="bi bi-info-circle me-2"></i>
                                没有找到模型。创建您的第一个模型吧！
                            </div>
                        </td>
                    </tr>
                `;
                return;
            }
            
            // 生成模型列表HTML
            let modelListHtml = '';
            data.items.forEach(model => {
                modelListHtml += `
                    <tr data-model-id="${model.id}">
                        <td>
                            <strong>${escapeHtml(model.name)}</strong>
                            ${model.is_public ? '<span class="badge bg-success ms-2">公开</span>' : ''}
                        </td>
                        <td>${model.framework}</td>
                        <td>${getStatusBadge(model.status)}</td>
                        <td>${model.endpoint_url ? escapeHtml(model.endpoint_url) : '-'}</td>
                        <td>${appUtils.formatDateTime(model.created_at)}</td>
                        <td>
                            <div class="btn-group btn-group-sm" role="group">
                                <button type="button" class="btn btn-outline-primary btn-view-model" 
                                        data-model-id="${model.id}" data-bs-toggle="tooltip" title="查看">
                                    <i class="bi bi-eye"></i>
                                </button>
                                <button type="button" class="btn btn-outline-secondary btn-edit-model" 
                                        data-model-id="${model.id}" data-bs-toggle="tooltip" title="编辑">
                                    <i class="bi bi-pencil"></i>
                                </button>
                                ${model.status === 'uploaded' ? `
                                    <button type="button" class="btn btn-outline-success btn-deploy-model" 
                                            data-model-id="${model.id}" data-bs-toggle="tooltip" title="部署">
                                        <i class="bi bi-cloud-upload"></i>
                                    </button>
                                ` : ''}
                                <button type="button" class="btn btn-outline-danger btn-delete-model" 
                                        data-model-id="${model.id}" data-bs-toggle="tooltip" title="删除">
                                    <i class="bi bi-trash"></i>
                                </button>
                            </div>
                        </td>
                    </tr>
                `;
            });
            
            modelListElement.innerHTML = modelListHtml;
            
            // 初始化工具提示
            const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
            tooltipTriggerList.map(function(tooltipTriggerEl) {
                return new bootstrap.Tooltip(tooltipTriggerEl);
            });
        })
        .catch(error => {
            console.error('获取模型列表错误:', error);
            if (loadingElement) loadingElement.style.display = 'none';
            
            modelListElement.innerHTML = `
                <tr>
                    <td colspan="6" class="text-center py-4">
                        <div class="alert alert-danger mb-0">
                            <i class="bi bi-exclamation-triangle me-2"></i>
                            获取模型列表失败: ${error.message}
                        </div>
                    </td>
                </tr>
            `;
        });
    }
    
    /**
     * 设置模型创建表单监听器
     */
    function setupModelCreateForm() {
        const modelForm = document.getElementById('modelForm');
        if (!modelForm) return;
        
        modelForm.addEventListener('submit', function(event) {
            event.preventDefault();
            
            // 获取表单数据
            const formData = new FormData(modelForm);
            const modelData = {
                name: formData.get('name'),
                description: formData.get('description'),
                framework: formData.get('framework'),
                version: formData.get('version') || '0.1.0',
                is_public: formData.get('is_public') === 'on'
            };
            
            // 发送创建请求
            const token = localStorage.getItem('access_token');
            
            fetch('/api/v1/models', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(modelData)
            })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(data => {
                        throw new Error(data.detail || '创建模型失败');
                    });
                }
                return response.json();
            })
            .then(data => {
                // 关闭模态框
                const modalElement = document.getElementById('createModelModal');
                const modal = bootstrap.Modal.getInstance(modalElement);
                modal.hide();
                
                // 显示成功消息
                showAlert('success', '模型创建成功！');
                
                // 重置表单
                modelForm.reset();
                
                // 刷新模型列表
                initModelList();
            })
            .catch(error => {
                console.error('创建模型错误:', error);
                showAlert('danger', error.message);
            });
        });
    }
    
    /**
     * 设置模型操作按钮监听器
     */
    function setupModelActions() {
        const modelListElement = document.getElementById('modelList');
        if (!modelListElement) return;
        
        // 使用事件委托处理按钮点击
        modelListElement.addEventListener('click', function(event) {
            // 查找最近的按钮祖先元素
            const button = event.target.closest('button');
            if (!button) return;
            
            const modelId = button.getAttribute('data-model-id');
            if (!modelId) return;
            
            // 根据按钮类确定操作类型
            if (button.classList.contains('btn-view-model')) {
                viewModel(modelId);
            } else if (button.classList.contains('btn-edit-model')) {
                editModel(modelId);
            } else if (button.classList.contains('btn-deploy-model')) {
                deployModel(modelId);
            } else if (button.classList.contains('btn-delete-model')) {
                deleteModel(modelId);
            }
        });
    }
    
    /**
     * 查看模型详情
     * @param {string} modelId - 模型ID
     */
    function viewModel(modelId) {
        const token = localStorage.getItem('access_token');
        
        fetch(`/api/v1/models/${modelId}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('获取模型详情失败');
            }
            return response.json();
        })
        .then(model => {
            // 填充模型详情模态框
            document.getElementById('modelDetailName').textContent = model.name;
            document.getElementById('modelDetailDescription').textContent = model.description || '无描述';
            document.getElementById('modelDetailFramework').textContent = model.framework;
            document.getElementById('modelDetailVersion').textContent = model.version;
            document.getElementById('modelDetailStatus').innerHTML = getStatusBadge(model.status);
            document.getElementById('modelDetailPublic').textContent = model.is_public ? '是' : '否';
            document.getElementById('modelDetailCreated').textContent = appUtils.formatDateTime(model.created_at);
            
            if (model.endpoint_url) {
                document.getElementById('modelDetailEndpoint').textContent = model.endpoint_url;
                document.getElementById('modelDetailEndpointRow').style.display = '';
            } else {
                document.getElementById('modelDetailEndpointRow').style.display = 'none';
            }
            
            // 显示模态框
            const modalElement = document.getElementById('viewModelModal');
            const modal = new bootstrap.Modal(modalElement);
            modal.show();
        })
        .catch(error => {
            console.error('获取模型详情错误:', error);
            showAlert('danger', error.message);
        });
    }
    
    /**
     * 编辑模型
     * @param {string} modelId - 模型ID
     */
    function editModel(modelId) {
        const token = localStorage.getItem('access_token');
        
        fetch(`/api/v1/models/${modelId}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('获取模型详情失败');
            }
            return response.json();
        })
        .then(model => {
            // 填充编辑表单
            const editForm = document.getElementById('editModelForm');
            editForm.elements['model_id'].value = model.id;
            editForm.elements['name'].value = model.name;
            editForm.elements['description'].value = model.description || '';
            editForm.elements['framework'].value = model.framework;
            editForm.elements['is_public'].checked = model.is_public;
            
            // 显示模态框
            const modalElement = document.getElementById('editModelModal');
            const modal = new bootstrap.Modal(modalElement);
            modal.show();
            
            // 设置保存按钮监听器
            editForm.onsubmit = function(event) {
                event.preventDefault();
                
                // 获取表单数据
                const formData = new FormData(editForm);
                const modelData = {
                    name: formData.get('name'),
                    description: formData.get('description'),
                    framework: formData.get('framework'),
                    is_public: formData.get('is_public') === 'on'
                };
                
                // 发送更新请求
                fetch(`/api/v1/models/${modelId}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify(modelData)
                })
                .then(response => {
                    if (!response.ok) {
                        return response.json().then(data => {
                            throw new Error(data.detail || '更新模型失败');
                        });
                    }
                    return response.json();
                })
                .then(data => {
                    // 关闭模态框
                    const modalInstance = bootstrap.Modal.getInstance(modalElement);
                    modalInstance.hide();
                    
                    // 显示成功消息
                    showAlert('success', '模型更新成功！');
                    
                    // 刷新模型列表
                    initModelList();
                })
                .catch(error => {
                    console.error('更新模型错误:', error);
                    showAlert('danger', error.message);
                });
            };
        })
        .catch(error => {
            console.error('获取模型详情错误:', error);
            showAlert('danger', error.message);
        });
    }
    
    /**
     * 部署模型
     * @param {string} modelId - 模型ID
     */
    function deployModel(modelId) {
        if (!confirm('确定要部署此模型吗？')) {
            return;
        }
        
        const token = localStorage.getItem('access_token');
        
        fetch(`/api/v1/models/${modelId}/deploy`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({}) // 可以添加部署配置
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.detail || '部署模型失败');
                });
            }
            return response.json();
        })
        .then(data => {
            // 显示成功消息
            showAlert('success', '模型部署成功！');
            
            // 刷新模型列表
            initModelList();
        })
        .catch(error => {
            console.error('部署模型错误:', error);
            showAlert('danger', error.message);
        });
    }
    
    /**
     * 删除模型
     * @param {string} modelId - 模型ID
     */
    function deleteModel(modelId) {
        if (!confirm('确定要删除此模型吗？此操作不可撤销！')) {
            return;
        }
        
        const token = localStorage.getItem('access_token');
        
        fetch(`/api/v1/models/${modelId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.detail || '删除模型失败');
                });
            }
            return response.json();
        })
        .then(data => {
            // 显示成功消息
            showAlert('success', '模型删除成功！');
            
            // 刷新模型列表
            initModelList();
        })
        .catch(error => {
            console.error('删除模型错误:', error);
            showAlert('danger', error.message);
        });
    }
    
    /**
     * 设置模型搜索功能
     */
    function setupModelSearch() {
        const searchForm = document.getElementById('modelSearchForm');
        if (!searchForm) return;
        
        searchForm.addEventListener('submit', function(event) {
            event.preventDefault();
            
            const searchQuery = document.getElementById('modelSearchInput').value.trim();
            initModelList(1, 10, searchQuery);
        });
        
        // 重置搜索
        const resetButton = document.getElementById('resetModelSearch');
        if (resetButton) {
            resetButton.addEventListener('click', function() {
                document.getElementById('modelSearchInput').value = '';
                initModelList();
            });
        }
    }
    
    /**
     * 设置分页功能
     */
    function setupPagination() {
        const paginationElement = document.getElementById('modelPagination');
        if (!paginationElement) return;
        
        paginationElement.addEventListener('click', function(event) {
            event.preventDefault();
            
            // 查找最近的分页链接
            const pageLink = event.target.closest('a.page-link');
            if (!pageLink) return;
            
            const page = pageLink.getAttribute('data-page');
            if (!page) return;
            
            // 获取当前搜索查询
            const searchQuery = document.getElementById('modelSearchInput')?.value.trim() || '';
            
            // 刷新模型列表
            initModelList(parseInt(page), 10, searchQuery);
        });
    }
    
    /**
     * 更新分页控件
     * @param {number} currentPage - 当前页码
     * @param {number} totalPages - 总页数
     * @param {number} totalItems - 总条目数
     */
    function updatePagination(currentPage, totalPages, totalItems) {
        const paginationElement = document.getElementById('modelPagination');
        if (!paginationElement) return;
        
        // 更新总条目数显示
        const totalElement = document.getElementById('modelTotal');
        if (totalElement) {
            totalElement.textContent = `共 ${totalItems} 个模型`;
        }
        
        // 如果只有一页，隐藏分页控件
        if (totalPages <= 1) {
            paginationElement.style.display = 'none';
            return;
        }
        
        paginationElement.style.display = 'flex';
        
        // 生成分页HTML
        let paginationHtml = '';
        
        // 上一页按钮
        paginationHtml += `
            <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
                <a class="page-link" href="#" data-page="${currentPage - 1}" aria-label="上一页">
                    <span aria-hidden="true">&laquo;</span>
                </a>
            </li>
        `;
        
        // 页码按钮
        const startPage = Math.max(1, currentPage - 2);
        const endPage = Math.min(totalPages, startPage + 4);
        
        for (let i = startPage; i <= endPage; i++) {
            paginationHtml += `
                <li class="page-item ${i === currentPage ? 'active' : ''}">
                    <a class="page-link" href="#" data-page="${i}">${i}</a>
                </li>
            `;
        }
        
        // 下一页按钮
        paginationHtml += `
            <li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
                <a class="page-link" href="#" data-page="${currentPage + 1}" aria-label="下一页">
                    <span aria-hidden="true">&raquo;</span>
                </a>
            </li>
        `;
        
        paginationElement.innerHTML = paginationHtml;
    }
    
    /**
     * 显示提示信息
     * @param {string} type - 提示类型：success, danger, warning, info
     * @param {string} message - 提示消息
     */
    function showAlert(type, message) {
        const alertsContainer = document.getElementById('alertsContainer');
        if (!alertsContainer) return;
        
        const alertId = 'alert-' + Date.now();
        const alertHtml = `
            <div id="${alertId}" class="alert alert-${type} alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="关闭"></button>
            </div>
        `;
        
        alertsContainer.innerHTML += alertHtml;
        
        // 5秒后自动关闭
        setTimeout(() => {
            const alertElement = document.getElementById(alertId);
            if (alertElement) {
                const alert = bootstrap.Alert.getOrCreateInstance(alertElement);
                alert.close();
            }
        }, 5000);
    }
    
    /**
     * 根据状态获取显示徽章
     * @param {string} status - 模型状态
     * @returns {string} 状态徽章HTML
     */
    function getStatusBadge(status) {
        const statusMap = {
            'uploading': '<span class="badge bg-info">上传中</span>',
            'uploaded': '<span class="badge bg-secondary">已上传</span>',
            'validating': '<span class="badge bg-warning">验证中</span>',
            'valid': '<span class="badge bg-success">已验证</span>',
            'invalid': '<span class="badge bg-danger">验证失败</span>',
            'deploying': '<span class="badge bg-primary">部署中</span>',
            'deployed': '<span class="badge bg-success">已部署</span>',
            'undeployed': '<span class="badge bg-secondary">未部署</span>',
            'archived': '<span class="badge bg-dark">已归档</span>'
        };
        
        return statusMap[status] || `<span class="badge bg-secondary">${status}</span>`;
    }
    
    /**
     * 转义HTML特殊字符
     * @param {string} text - 需要转义的文本
     * @returns {string} 转义后的文本
     */
    function escapeHtml(text) {
        if (!text) return '';
        
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        
        return text.replace(/[&<>"']/g, function(m) { return map[m]; });
    }
})(); 