/**
 * AI模型管理平台主JavaScript文件
 * 
 * 提供全局功能，包括认证、导航和工具函数
 */

// 立即执行函数，避免全局变量污染
(function() {
    'use strict';
    
    // 页面加载完成后执行
    document.addEventListener('DOMContentLoaded', function() {
        // 初始化工具提示
        initTooltips();
        
        // 处理认证状态
        handleAuth();
        
        // 设置导航活动项
        setActiveNavItem();
        
        // 设置退出登录监听器
        setupLogout();
    });
    
    /**
     * 初始化页面上的所有工具提示
     */
    function initTooltips() {
        // 查找所有有data-bs-toggle="tooltip"属性的元素
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function(tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
    
    /**
     * 处理用户认证状态
     */
    function handleAuth() {
        const token = localStorage.getItem('access_token');
        const userMenu = document.getElementById('userDropdown');
        const logoutBtn = document.getElementById('logoutBtn');
        
        // 当前页面路径
        const path = window.location.pathname;
        
        // 不需要认证的路径
        const publicPaths = ['/', '/login', '/register'];
        
        // 检查是否在公开页面
        const isPublicPage = publicPaths.includes(path);
        
        if (token) {
            // 已登录
            if (userMenu) {
                // 获取用户信息
                fetchUserInfo(token);
            }
            
            // 如果在登录或注册页面，重定向到仪表盘
            if (path === '/login' || path === '/register') {
                window.location.href = '/dashboard';
            }
        } else {
            // 未登录
            if (!isPublicPage) {
                // 如果不在公开页面，重定向到登录页
                window.location.href = '/login';
            }
        }
    }
    
    /**
     * 获取用户信息
     * @param {string} token - 用户访问令牌
     */
    async function fetchUserInfo(token) {
        try {
            const userNameElem = document.querySelector('.user-name');
            if (!userNameElem) return;
            
            // 设置默认请求头
            axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
            
            // 获取用户信息
            const response = await axios.get('/api/v1/users/me');
            const userData = response.data;
            
            // 更新用户名
            userNameElem.textContent = userData.username;
        } catch (error) {
            console.error('获取用户信息失败:', error);
            if (error.response && error.response.status === 401) {
                // 令牌无效或过期，清除令牌并重定向到登录页
                localStorage.removeItem('access_token');
                window.location.href = '/login';
            }
        }
    }
    
    /**
     * 设置当前导航活动项
     */
    function setActiveNavItem() {
        const currentPath = window.location.pathname;
        const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
        
        navLinks.forEach(link => {
            const href = link.getAttribute('href');
            if (href === currentPath) {
                link.classList.add('active');
            } else {
                link.classList.remove('active');
            }
        });
    }
    
    /**
     * 设置退出登录监听器
     */
    function setupLogout() {
        const logoutBtn = document.getElementById('logoutBtn');
        if (!logoutBtn) return;
        
        logoutBtn.addEventListener('click', function(event) {
            event.preventDefault();
            
            // 清除令牌
            localStorage.removeItem('access_token');
            
            // 重定向到登录页
            window.location.href = '/login';
        });
    }
    
    // 导出工具函数
    window.appUtils = {
        /**
         * 格式化日期时间字符串
         * @param {string} dateString - ISO日期时间字符串
         * @param {boolean} includeTime - 是否包含时间
         * @returns {string} 格式化的日期时间字符串
         */
        formatDateTime: function(dateString, includeTime = true) {
            if (!dateString) return '';
            
            const date = new Date(dateString);
            const options = {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit'
            };
            
            if (includeTime) {
                options.hour = '2-digit';
                options.minute = '2-digit';
                options.second = '2-digit';
            }
            
            return date.toLocaleString('zh-CN', options);
        },
        
        /**
         * 处理API错误，显示适当的错误消息
         * @param {Error} error - 错误对象，通常来自axios捕获的错误
         * @returns {string} 错误消息
         */
        handleApiError: function(error) {
            console.error('API错误:', error);
            
            if (error.response) {
                // 服务器响应，但状态码不在2xx范围内
                if (error.response.status === 401) {
                    localStorage.removeItem('access_token');
                    window.location.href = '/login';
                    return '登录已过期，请重新登录';
                } else if (error.response.data && error.response.data.detail) {
                    return error.response.data.detail;
                }
                return `请求失败 (${error.response.status})`;
            } else if (error.request) {
                // 请求已发送，但未收到响应
                return '无法连接到服务器，请检查网络连接';
            } else {
                // 请求配置时出错
                return error.message || '发生未知错误';
            }
        }
    };
})(); 