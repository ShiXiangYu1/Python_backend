/**
 * API密钥管理页面JavaScript
 * 
 * 处理API密钥的创建、列表展示、停用和删除功能
 */

// 立即执行函数，避免全局变量污染
(function() {
    'use strict';
    
    // 当前页面状态
    const state = {
        page: 1,
        pageSize: 10,
        totalPages: 1
    };
    
    // 页面加载完成后执行
    document.addEventListener('DOMContentLoaded', function() {
        // 检查是否登录
        const token = localStorage.getItem('access_token');
        if (!token) {
            window.location.href = '/login';
            return;
        }
        
        // 设置请求头
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
        
        // 加载API密钥数据
        loadApiKeys();
        
        // 设置创建API密钥按钮
        setupCreateApiKey();
        
        // 设置复制API密钥按钮
        setupCopyApiKey();
        
        // 设置分页事件处理
        setupPagination();
    });
    
    /**
     * 加载API密钥列表数据
     */
    function loadApiKeys() {
        // 清空表格内容并显示加载状态
        const apiKeysTable = document.getElementById('apiKeysTable');
        if (!apiKeysTable) return;
        
        apiKeysTable.innerHTML = `
            <tr>
                <td colspan="7" class="text-center py-4">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">正在加载...</span>
                    </div>
                </td>
            </tr>
        `;
        
        // 构建查询参数
        const url = `/api/v1/api-keys?page=${state.page}&page_size=${state.pageSize}`;
        
        // 发送请求
        axios.get(url)
            .then(response => {
                const { items, total, page, page_size } = response.data;
                
                // 更新总数
                const totalElement = document.getElementById('totalApiKeys');
                if (totalElement) {
                    totalElement.textContent = total;
                }
                
                // 计算总页数
                state.totalPages = Math.ceil(total / page_size);
                
                // 渲染API密钥列表
                if (items.length > 0) {
                    let html = '';
                    items.forEach(key => {
                        const created = appUtils.formatDateTime(key.created_at);
                        const expires = key.expires_at ? appUtils.formatDateTime(key.expires_at) : '永不过期';
                        const lastUsed = key.last_used_at ? appUtils.formatDateTime(key.last_used_at) : '从未使用';
                        
                        html += `
                            <tr>
                                <td>${escapeHtml(key.name)}</td>
                                <td>${created}</td>
                                <td>${expires}</td>
                                <td>${lastUsed}</td>
                                <td>
                                    <span class="badge bg-${key.is_active ? 'success' : 'danger'}">
                                        ${key.is_active ? '激活' : '停用'}
                                    </span>
                                </td>
                                <td>
                                    ${formatScopes(key.scopes)}
                                </td>
                                <td>
                                    <div class="btn-group">
                                        ${key.is_active ? 
                                            `<button class="btn btn-sm btn-outline-warning" onclick="deactivateApiKey('${key.id}')">停用</button>` : 
                                            `<button class="btn btn-sm btn-outline-success" onclick="activateApiKey('${key.id}')">激活</button>`
                                        }
                                        <button class="btn btn-sm btn-outline-danger" onclick="deleteApiKey('${key.id}')">删除</button>
                                    </div>
                                </td>
                            </tr>
                        `;
                    });
                    apiKeysTable.innerHTML = html;
                } else {
                    apiKeysTable.innerHTML = `
                        <tr>
                            <td colspan="7" class="text-center py-4">暂无API密钥</td>
                        </tr>
                    `;
                }
                
                // 生成分页
                renderPagination();
            })
            .catch(error => {
                console.error('加载API密钥失败:', error);
                const errorMessage = appUtils.handleApiError(error);
                
                apiKeysTable.innerHTML = `
                    <tr>
                        <td colspan="7" class="text-center py-4 text-danger">
                            加载失败: ${errorMessage}
                        </td>
                    </tr>
                `;
            });
    }
    
    /**
     * 设置创建API密钥按钮
     */
    function setupCreateApiKey() {
        const createBtn = document.getElementById('createApiKeyBtn');
        if (!createBtn) return;
        
        createBtn.addEventListener('click', function() {
            const errorElem = document.getElementById('createApiKeyError');
            if (errorElem) {
                errorElem.classList.add('d-none');
            }
            
            const form = document.getElementById('createApiKeyForm');
            if (!form) return;
            
            // 获取所选范围
            const scopes = [];
            if (document.getElementById('scopeRead').checked) scopes.push('read');
            if (document.getElementById('scopeWrite').checked) scopes.push('write');
            if (document.getElementById('scopeAdmin').checked) scopes.push('admin');
            
            // 计算过期时间
            let expiresAt = null;
            const expiryDays = document.getElementById('apiKeyExpiry').value;
            if (expiryDays !== 'never') {
                const date = new Date();
                date.setDate(date.getDate() + parseInt(expiryDays, 10));
                expiresAt = date.toISOString();
            }
            
            const keyData = {
                name: document.getElementById('apiKeyName').value,
                scopes: scopes.join(','),
                expires_at: expiresAt
            };
            
            // 验证表单
            if (!keyData.name) {
                if (errorElem) {
                    errorElem.textContent = '请输入密钥名称';
                    errorElem.classList.remove('d-none');
                }
                return;
            }
            
            if (scopes.length === 0) {
                if (errorElem) {
                    errorElem.textContent = '请至少选择一个权限范围';
                    errorElem.classList.remove('d-none');
                }
                return;
            }
            
            // 发送请求
            axios.post('/api/v1/api-keys', keyData)
                .then(response => {
                    // 关闭创建模态框
                    const createModal = bootstrap.Modal.getInstance(document.getElementById('createModelModal'));
                    if (createModal) {
                        createModal.hide();
                    }
                    
                    // 显示密钥值
                    const newKeyInput = document.getElementById('newApiKeyValue');
                    const apiKeyExample = document.getElementById('apiKeyExample');
                    
                    if (newKeyInput) newKeyInput.value = response.data.key;
                    if (apiKeyExample) apiKeyExample.textContent = response.data.key;
                    
                    // 显示密钥模态框
                    const showModal = new bootstrap.Modal(document.getElementById('showApiKeyModal'));
                    showModal.show();
                    
                    // 重新加载API密钥列表
                    loadApiKeys();
                    
                    // 清空表单
                    form.reset();
                    document.getElementById('scopeRead').checked = true;
                })
                .catch(error => {
                    console.error('创建API密钥失败:', error);
                    const errorMessage = appUtils.handleApiError(error);
                    
                    if (errorElem) {
                        errorElem.textContent = errorMessage;
                        errorElem.classList.remove('d-none');
                    }
                });
        });
    }
    
    /**
     * 设置复制API密钥按钮
     */
    function setupCopyApiKey() {
        const copyBtn = document.getElementById('copyApiKeyBtn');
        if (!copyBtn) return;
        
        copyBtn.addEventListener('click', function() {
            const keyInput = document.getElementById('newApiKeyValue');
            if (!keyInput) return;
            
            keyInput.select();
            document.execCommand('copy');
            
            // 更新按钮文本
            this.innerHTML = '<svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg> 已复制';
            
            // 2秒后恢复
            setTimeout(() => {
                this.innerHTML = '<svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"></path></svg> 复制';
            }, 2000);
        });
    }
    
    /**
     * 设置分页事件处理
     */
    function setupPagination() {
        const pagination = document.getElementById('pagination');
        if (!pagination) return;
        
        // 使用事件委托处理分页点击事件
        pagination.addEventListener('click', function(event) {
            event.preventDefault();
            
            // 查找最近的链接元素
            const link = event.target.closest('a.page-link');
            if (!link) return;
            
            // 获取页码
            const page = parseInt(link.getAttribute('data-page'), 10);
            if (isNaN(page) || page < 1 || page > state.totalPages || page === state.page) {
                return;
            }
            
            // 更新当前页
            state.page = page;
            
            // 加载API密钥
            loadApiKeys();
        });
    }
    
    /**
     * 渲染分页控件
     */
    function renderPagination() {
        const pagination = document.getElementById('pagination');
        if (!pagination) return;
        
        if (state.totalPages <= 1) {
            pagination.innerHTML = '';
            return;
        }
        
        let html = `
            <li class="page-item ${state.page === 1 ? 'disabled' : ''}">
                <a class="page-link" href="#" data-page="${state.page - 1}" aria-label="上一页">
                    <span aria-hidden="true">&laquo;</span>
                </a>
            </li>
        `;
        
        // 显示最多5个页码
        const maxPages = 5;
        let startPage = Math.max(1, state.page - Math.floor(maxPages / 2));
        let endPage = Math.min(state.totalPages, startPage + maxPages - 1);
        
        if (endPage - startPage + 1 < maxPages) {
            startPage = Math.max(1, endPage - maxPages + 1);
        }
        
        for (let i = startPage; i <= endPage; i++) {
            html += `
                <li class="page-item ${i === state.page ? 'active' : ''}">
                    <a class="page-link" href="#" data-page="${i}">${i}</a>
                </li>
            `;
        }
        
        html += `
            <li class="page-item ${state.page === state.totalPages ? 'disabled' : ''}">
                <a class="page-link" href="#" data-page="${state.page + 1}" aria-label="下一页">
                    <span aria-hidden="true">&raquo;</span>
                </a>
            </li>
        `;
        
        pagination.innerHTML = html;
    }
    
    /**
     * 格式化权限范围
     * @param {string} scopes - 权限范围，逗号分隔的字符串
     * @returns {string} HTML格式的权限徽章
     */
    function formatScopes(scopes) {
        if (!scopes) return '';
        
        const scopeArray = scopes.split(',');
        let html = '';
        
        if (scopeArray.includes('read')) {
            html += '<span class="badge bg-info me-1">读取</span>';
        }
        if (scopeArray.includes('write')) {
            html += '<span class="badge bg-primary me-1">写入</span>';
        }
        if (scopeArray.includes('admin')) {
            html += '<span class="badge bg-danger me-1">管理</span>';
        }
        
        return html;
    }
    
    /**
     * HTML转义函数
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
    
    // 全局函数：停用API密钥
    window.deactivateApiKey = function(keyId) {
        if (!confirm('确定要停用此API密钥吗？停用后将无法使用此密钥进行API访问。')) {
            return;
        }
        
        axios.post(`/api/v1/api-keys/${keyId}/deactivate`)
            .then(() => {
                // 显示成功消息
                showAlert('success', 'API密钥已成功停用');
                
                // 重新加载API密钥列表
                loadApiKeys();
            })
            .catch(error => {
                console.error('停用API密钥失败:', error);
                const errorMessage = appUtils.handleApiError(error);
                showAlert('danger', '停用失败: ' + errorMessage);
            });
    };
    
    // 全局函数：激活API密钥
    window.activateApiKey = function(keyId) {
        axios.put(`/api/v1/api-keys/${keyId}`, {
            is_active: true
        })
            .then(() => {
                // 显示成功消息
                showAlert('success', 'API密钥已成功激活');
                
                // 重新加载API密钥列表
                loadApiKeys();
            })
            .catch(error => {
                console.error('激活API密钥失败:', error);
                const errorMessage = appUtils.handleApiError(error);
                showAlert('danger', '激活失败: ' + errorMessage);
            });
    };
    
    // 全局函数：删除API密钥
    window.deleteApiKey = function(keyId) {
        if (!confirm('确定要删除此API密钥吗？此操作不可撤销，所有使用此密钥的应用将无法访问API。')) {
            return;
        }
        
        axios.delete(`/api/v1/api-keys/${keyId}`)
            .then(() => {
                // 显示成功消息
                showAlert('success', 'API密钥已成功删除');
                
                // 重新加载API密钥列表
                loadApiKeys();
            })
            .catch(error => {
                console.error('删除API密钥失败:', error);
                const errorMessage = appUtils.handleApiError(error);
                showAlert('danger', '删除失败: ' + errorMessage);
            });
    };
    
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
})(); 