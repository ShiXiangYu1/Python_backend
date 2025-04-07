# Nginx 配置目录

本目录包含项目使用的Nginx Web服务器配置文件。

## 目录结构

- `conf.d/` - 包含Nginx的具体配置文件
  - `app.conf` - 主应用程序的Nginx配置
  - `prometheus.conf` - Prometheus监控系统的反向代理配置
  - `grafana.conf` - Grafana监控面板的反向代理配置

## 配置说明

### 主应用配置 (app.conf)

此配置文件设置了主应用程序的代理规则，包括：

- 将HTTP请求转发到FastAPI应用
- 设置静态文件缓存
- 配置SSL/TLS设置（生产环境）
- 添加安全HTTP头
- 配置访问日志格式

### 监控系统配置

- `prometheus.conf` - 配置Prometheus监控系统的访问规则和认证
- `grafana.conf` - 配置Grafana监控面板的访问规则和代理设置

## 使用方法

在Docker环境中，这些配置文件会被自动挂载到Nginx容器中。如果需要在非Docker环境中使用：

1. 将配置文件复制到Nginx的配置目录（通常是 `/etc/nginx/conf.d/`）
2. 重新加载Nginx配置：
   ```
   sudo nginx -t       # 测试配置语法
   sudo nginx -s reload # 重新加载配置
   ```

## 环境变量

配置文件中可能包含以下环境变量的引用，需要在部署时设置：

- `API_HOST` - API服务的主机名
- `API_PORT` - API服务的端口
- `GRAFANA_HOST` - Grafana服务的主机名
- `GRAFANA_PORT` - Grafana服务的端口
- `PROMETHEUS_HOST` - Prometheus服务的主机名
- `PROMETHEUS_PORT` - Prometheus服务的端口 