/**
 * 仪表盘页面JavaScript
 * 
 * 处理仪表盘数据的加载和展示
 */

// 立即执行函数，避免全局变量污染
(function() {
    'use strict';
    
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
        
        // 加载用户信息
        loadUserInfo();
        
        // 加载统计数据
        loadStatistics();
        
        // 加载最近模型
        loadRecentModels();
        
        // 加载API密钥列表
        loadApiKeys();
    });
    
    /**
     * 加载用户信息
     */
    function loadUserInfo() {
        axios.get('/api/v1/users/me')
            .then(response => {
                const userData = response.data;
                
                // 更新用户名
                const userNameElem = document.getElementById('userName');
                if (userNameElem) {
                    userNameElem.textContent = userData.username;
                }
            })
            .catch(error => {
                console.error('获取用户信息失败:', error);
                if (error.response && error.response.status === 401) {
                    // 未授权，跳转到登录页
                    localStorage.removeItem('access_token');
                    window.location.href = '/login';
                }
            });
    }
    
    /**
     * 加载统计数据
     */
    function loadStatistics() {
        // 并行请求模型和API密钥数据
        Promise.all([
            axios.get('/api/v1/models?page=1&page_size=1'),
            axios.get('/api/v1/api-keys?page=1&page_size=1')
        ])
            .then(([modelsResponse, apiKeysResponse]) => {
                // 更新模型总数
                const totalModelsElem = document.getElementById('totalModels');
                if (totalModelsElem) {
                    totalModelsElem.textContent = modelsResponse.data.total || 0;
                }
                
                // 获取已部署模型数量
                getDeployedModelsCount()
                    .then(count => {
                        const deployedModelsElem = document.getElementById('deployedModels');
                        if (deployedModelsElem) {
                            deployedModelsElem.textContent = count;
                        }
                    });
                
                // 更新API密钥总数
                const totalApiKeysElem = document.getElementById('totalApiKeys');
                if (totalApiKeysElem) {
                    totalApiKeysElem.textContent = apiKeysResponse.data.total || 0;
                }
                
                // 模拟API调用次数
                const totalApiCallsElem = document.getElementById('totalApiCalls');
                if (totalApiCallsElem) {
                    // 这里使用模拟数据，实际项目中应从后端获取
                    const randomCalls = Math.floor(Math.random() * 1000);
                    totalApiCallsElem.textContent = randomCalls;
                }
            })
            .catch(error => {
                console.error('加载统计数据失败:', error);
                if (error.response && error.response.status === 401) {
                    // 未授权，跳转到登录页
                    localStorage.removeItem('access_token');
                    window.location.href = '/login';
                }
            });
    }
    
    /**
     * 获取已部署模型数量
     * @returns {Promise<number>} 已部署模型数量的Promise
     */
    function getDeployedModelsCount() {
        return axios.get('/api/v1/models?status=deployed&page=1&page_size=1')
            .then(response => {
                return response.data.total || 0;
            })
            .catch(error => {
                console.error('获取已部署模型数量失败:', error);
                return 0;
            });
    }
    
    /**
     * 加载最近模型列表
     */
    function loadRecentModels() {
        const recentModelsTable = document.getElementById('recentModels');
        if (!recentModelsTable) return;
        
        // 显示加载状态
        recentModelsTable.innerHTML = `
            <tr>
                <td colspan="5" class="text-center">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">正在加载...</span>
                    </div>
                </td>
            </tr>
        `;
        
        // 获取最近5个模型
        axios.get('/api/v1/models?page=1&page_size=5&sort=-created_at')
            .then(response => {
                const models = response.data.items;
                
                if (models.length === 0) {
                    recentModelsTable.innerHTML = `
                        <tr>
                            <td colspan="5" class="text-center">暂无模型数据</td>
                        </tr>
                    `;
                    return;
                }
                
                // 生成模型列表HTML
                let html = '';
                models.forEach(model => {
                    html += `
                        <tr>
                            <td>${escapeHtml(model.name)}</td>
                            <td><span class="badge bg-${getStatusBadgeColor(model.status)}">${getStatusText(model.status)}</span></td>
                            <td>${escapeHtml(model.framework)}</td>
                            <td>${appUtils.formatDateTime(model.created_at, false)}</td>
                            <td>
                                <a href="/models/${model.id}" class="btn btn-sm btn-outline-primary">查看</a>
                            </td>
                        </tr>
                    `;
                });
                
                recentModelsTable.innerHTML = html;
            })
            .catch(error => {
                console.error('加载最近模型失败:', error);
                recentModelsTable.innerHTML = `
                    <tr>
                        <td colspan="5" class="text-center text-danger">
                            加载失败: ${appUtils.handleApiError(error)}
                        </td>
                    </tr>
                `;
            });
    }
    
    /**
     * 加载API密钥列表
     */
    function loadApiKeys() {
        const apiKeysList = document.getElementById('apiKeysList');
        if (!apiKeysList) return;
        
        // 显示加载状态
        apiKeysList.innerHTML = `
            <li class="list-group-item text-center">
                <div class="spinner-border spinner-border-sm text-primary" role="status">
                    <span class="visually-hidden">正在加载...</span>
                </div>
            </li>
        `;
        
        // 获取最近3个API密钥
        axios.get('/api/v1/api-keys?page=1&page_size=3&sort=-created_at')
            .then(response => {
                const keys = response.data.items;
                
                if (keys.length === 0) {
                    apiKeysList.innerHTML = `
                        <li class="list-group-item text-center">暂无API密钥</li>
                    `;
                    return;
                }
                
                // 生成API密钥列表HTML
                let html = '';
                keys.forEach(key => {
                    const lastUsed = key.last_used_at ? 
                        appUtils.formatDateTime(key.last_used_at, false) : 
                        '从未使用';
                        
                    html += `
                        <li class="list-group-item">
                            <div class="d-flex justify-content-between align-items-center">
                                <div>
                                    <h6 class="mb-0">${escapeHtml(key.name)}</h6>
                                    <small class="text-muted">最后使用: ${lastUsed}</small>
                                </div>
                                <span class="badge bg-${key.is_active ? 'success' : 'danger'} rounded-pill">
                                    ${key.is_active ? '激活' : '停用'}
                                </span>
                            </div>
                        </li>
                    `;
                });
                
                apiKeysList.innerHTML = html;
            })
            .catch(error => {
                console.error('加载API密钥失败:', error);
                apiKeysList.innerHTML = `
                    <li class="list-group-item text-center text-danger">
                        加载失败: ${appUtils.handleApiError(error)}
                    </li>
                `;
            });
    }
    
    /**
     * 获取状态对应的徽章颜色
     * @param {string} status - 模型状态
     * @returns {string} 对应的Bootstrap颜色类名
     */
    function getStatusBadgeColor(status) {
        switch(status) {
            case 'uploaded': return 'success';
            case 'uploading': return 'warning';
            case 'deployed': return 'primary';
            case 'failed': return 'danger';
            default: return 'secondary';
        }
    }
    
    /**
     * 获取状态对应的中文文本
     * @param {string} status - 模型状态
     * @returns {string} 状态的中文描述
     */
    function getStatusText(status) {
        switch(status) {
            case 'uploaded': return '已上传';
            case 'uploading': return '上传中';
            case 'deployed': return '已部署';
            case 'failed': return '失败';
            default: return '未知';
        }
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
})(); 