# 监控系统目录

本目录包含项目监控系统的配置文件和仪表盘定义。

## 目录结构

- `grafana/` - Grafana监控面板配置
  - `dashboards/` - 预定义的仪表盘JSON定义
  - `provisioning/` - Grafana自动配置文件
- `prometheus/` - Prometheus监控系统配置
  - `prometheus.yml` - 主配置文件
  - `alert.rules` - 告警规则定义
  - `targets/` - 监控目标配置

## 监控系统说明

本项目使用Prometheus和Grafana构建完整的监控系统，用于收集和可视化以下指标：

1. **应用指标**
   - API请求计数和响应时间
   - 任务队列长度和处理时间
   - 自定义业务指标

2. **系统指标**
   - CPU、内存、磁盘使用情况
   - 网络流量和连接数
   - 容器资源使用情况

3. **数据库指标**
   - 连接池状态
   - 查询执行时间
   - 事务和锁信息

## 使用方法

### 启动监控系统

使用Docker Compose启动监控系统：

```bash
docker-compose -f docker-compose.monitoring.yml up -d
```

### 访问监控界面

- Grafana: http://localhost:3000 (默认用户名/密码: admin/admin)
- Prometheus: http://localhost:9090

### 添加新的监控目标

1. 在`prometheus/targets/`目录中添加新的目标配置文件
2. 在`prometheus.yml`中引用新的配置文件
3. 重启Prometheus服务：
   ```bash
   docker-compose -f docker-compose.monitoring.yml restart prometheus
   ```

### 添加新的仪表盘

1. 在Grafana界面创建并保存仪表盘
2. 导出仪表盘JSON定义
3. 将JSON文件保存到`grafana/dashboards/`目录
4. 在`grafana/provisioning/dashboards/`中添加引用

## 告警配置

告警规则定义在`prometheus/alert.rules`文件中，支持以下类型的告警：

- 高CPU和内存使用率
- API端点响应时间超阈值
- 服务可用性下降
- 任务队列堆积
- 数据库连接池饱和

告警可以通过电子邮件、Slack、钉钉等方式发送通知，配置位于`prometheus/alertmanager.yml`。

## 自定义指标

应用程序通过`/metrics`端点暴露自定义指标，使用`app/core/metrics.py`模块实现。要添加新的指标：

1. 在`metrics.py`中定义新的指标
2. 在相应的业务代码中记录指标
3. 确保`prometheus.yml`中已配置抓取应用的`/metrics`端点 