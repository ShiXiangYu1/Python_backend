/**
 * 用户资料页面JavaScript
 * 
 * 处理用户个人资料查看和修改功能
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
        
        // 加载用户资料
        loadUserProfile();
        
        // 设置更新资料表单提交事件
        setupProfileForm();
        
        // 设置修改密码表单提交事件
        setupChangePasswordForm();
    });
    
    /**
     * 加载用户资料
     */
    function loadUserProfile() {
        // 获取用户资料
        axios.get('/api/v1/users/me')
            .then(response => {
                const userData = response.data;
                
                // 填充页面信息
                fillProfileInfo(userData);
                
                // 填充表单
                fillProfileForm(userData);
            })
            .catch(error => {
                console.error('获取用户资料失败:', error);
                const errorMessage = appUtils.handleApiError(error);
                showAlert('danger', '获取用户资料失败: ' + errorMessage);
            });
    }
    
    /**
     * 填充页面上的用户资料信息
     * @param {Object} userData - 用户数据
     */
    function fillProfileInfo(userData) {
        // 设置用户名
        const usernameElement = document.getElementById('profileUsername');
        if (usernameElement) {
            usernameElement.textContent = userData.username;
        }
        
        // 设置邮箱
        const emailElement = document.getElementById('profileEmail');
        if (emailElement) {
            emailElement.textContent = userData.email;
        }
        
        // 设置角色
        const roleElement = document.getElementById('profileRole');
        if (roleElement) {
            roleElement.textContent = userData.is_admin ? '管理员' : '普通用户';
        }
        
        // 设置创建时间
        const createdElement = document.getElementById('profileCreated');
        if (createdElement) {
            createdElement.textContent = appUtils.formatDateTime(userData.created_at);
        }
        
        // 设置最后登录时间
        const lastLoginElement = document.getElementById('profileLastLogin');
        if (lastLoginElement) {
            lastLoginElement.textContent = userData.last_login_at ? 
                appUtils.formatDateTime(userData.last_login_at) : 
                '从未登录';
        }
    }
    
    /**
     * 填充更新资料表单
     * @param {Object} userData - 用户数据
     */
    function fillProfileForm(userData) {
        const form = document.getElementById('updateProfileForm');
        if (!form) return;
        
        // 设置表单字段值
        const usernameInput = form.querySelector('[name="username"]');
        if (usernameInput) usernameInput.value = userData.username;
        
        const emailInput = form.querySelector('[name="email"]');
        if (emailInput) emailInput.value = userData.email;
        
        const fullNameInput = form.querySelector('[name="full_name"]');
        if (fullNameInput) fullNameInput.value = userData.full_name || '';
    }
    
    /**
     * 设置更新资料表单提交事件
     */
    function setupProfileForm() {
        const form = document.getElementById('updateProfileForm');
        if (!form) return;
        
        form.addEventListener('submit', function(event) {
            event.preventDefault();
            
            // 获取表单数据
            const formData = new FormData(form);
            const userData = {
                username: formData.get('username'),
                email: formData.get('email'),
                full_name: formData.get('full_name')
            };
            
            // 验证表单
            if (!userData.username) {
                showAlert('danger', '用户名不能为空');
                return;
            }
            
            if (!userData.email) {
                showAlert('danger', '邮箱不能为空');
                return;
            }
            
            // 发送更新请求
            axios.put('/api/v1/users/me', userData)
                .then(response => {
                    // 更新成功
                    showAlert('success', '个人资料更新成功');
                    
                    // 重新加载用户资料
                    loadUserProfile();
                })
                .catch(error => {
                    console.error('更新用户资料失败:', error);
                    const errorMessage = appUtils.handleApiError(error);
                    showAlert('danger', '更新个人资料失败: ' + errorMessage);
                });
        });
    }
    
    /**
     * 设置修改密码表单提交事件
     */
    function setupChangePasswordForm() {
        const form = document.getElementById('changePasswordForm');
        if (!form) return;
        
        form.addEventListener('submit', function(event) {
            event.preventDefault();
            
            // 获取表单数据
            const formData = new FormData(form);
            const passwordData = {
                current_password: formData.get('current_password'),
                new_password: formData.get('new_password'),
                confirm_password: formData.get('confirm_password')
            };
            
            // 验证表单
            if (!passwordData.current_password) {
                showAlert('danger', '请输入当前密码');
                return;
            }
            
            if (!passwordData.new_password) {
                showAlert('danger', '请输入新密码');
                return;
            }
            
            if (passwordData.new_password.length < 8) {
                showAlert('danger', '新密码长度必须至少为8个字符');
                return;
            }
            
            if (passwordData.new_password !== passwordData.confirm_password) {
                showAlert('danger', '两次输入的新密码不一致');
                return;
            }
            
            // 发送修改密码请求
            axios.post('/api/v1/users/me/change-password', {
                current_password: passwordData.current_password,
                new_password: passwordData.new_password
            })
                .then(response => {
                    // 修改成功
                    showAlert('success', '密码修改成功');
                    
                    // 清空表单
                    form.reset();
                })
                .catch(error => {
                    console.error('修改密码失败:', error);
                    const errorMessage = appUtils.handleApiError(error);
                    showAlert('danger', '修改密码失败: ' + errorMessage);
                });
        });
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
})(); 