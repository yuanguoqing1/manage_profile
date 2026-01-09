# Implementation Plan: 火车票查询系统

## Overview

本实施计划将火车票查询系统的开发分解为增量式的编码任务。每个任务都建立在前面任务的基础上，确保系统逐步完善。实施将使用Python FastAPI作为后端，Vue 3作为前端，Redis作为缓存层。

## Tasks

- [x] 1. 设置项目基础结构和依赖
  - 更新backend/requirements.txt添加必要的依赖（httpx用于HTTP请求）
  - 创建app/services/train_service.py文件结构
  - 创建app/api/routes/train.py路由文件
  - 创建app/core/cache.py缓存管理器
  - 在app/api/router.py中注册train路由
  - _Requirements: 9.1_

- [ ] 2. 实现缓存管理器
  - [x] 2.1 实现CacheManager类
    - 实现get、set、delete方法
    - 实现generate_cache_key方法用于生成一致的缓存键
    - 添加错误处理确保缓存失败不影响主流程
    - _Requirements: 8.1, 8.2, 8.3_
  
  - [ ]* 2.2 编写CacheManager的属性测试
    - **Property 17: 缓存存储规则** - 验证成功查询被缓存5分钟
    - **Property 18: 缓存命中规则** - 验证相同查询返回缓存数据
    - **Property 19: 缓存过期重新请求** - 验证缓存过期后重新请求
    - _Requirements: 8.1, 8.2, 8.3_

- [x] 3. 实现数据模型
  - [x] 3.1 创建数据模型类
    - 在app/models/创建train.py
    - 实现Station、SeatInfo、TrainInfo、TrainQueryResponse模型
    - 实现QueryHistory模型用于保存查询历史
    - 添加Pydantic验证器
    - _Requirements: 1.2, 4.1, 4.2, 6.1_
  
  - [ ]* 3.2 编写数据模型的单元测试
    - 测试模型验证规则
    - 测试模型序列化和反序列化
    - _Requirements: 1.2, 4.1, 4.2_

- [x] 4. 实现12306 API集成
  - [x] 4.1 实现站点数据加载和搜索
    - 在TrainService中实现load_stations方法加载12306站点数据
    - 实现search_stations方法支持名称和拼音搜索
    - 解析12306的station_name.js文件格式
    - _Requirements: 1.1, 1.4_
  
  - [ ]* 4.2 编写站点搜索的属性测试
    - **Property 1: 站点搜索匹配性** - 验证搜索结果都包含关键字
    - **Property 2: 站点信息完整性** - 验证站点显示包含名称和代码
    - _Requirements: 1.1, 1.2, 1.4_
  
  - [x] 4.3 实现车次查询功能
    - 实现query_trains方法调用12306查询接口
    - 配置正确的请求头和参数
    - 实现超时和重试逻辑
    - _Requirements: 3.1, 3.2_
  
  - [ ]* 4.4 编写车次查询的属性测试
    - **Property 5: 查询触发API调用** - 验证有效参数触发API调用
    - **Property 6: 查询结果完整性** - 验证返回所有车次信息
    - _Requirements: 3.1, 3.2_

- [x] 5. 实现数据解析逻辑
  - [x] 5.1 实现12306数据解析器
    - 实现parse_train_data函数解析12306的管道分隔格式
    - 实现parse_seat_info函数解析座位信息
    - 处理各种座位类型（商务座、一等座、二等座、硬座、硬卧、软卧）
    - 添加健壮的错误处理
    - _Requirements: 3.5, 4.2, 5.1, 5.2_
  
  - [ ]* 5.2 编写数据解析的属性测试
    - **Property 8: 12306数据解析正确性** - 验证解析后包含所有必需字段
    - **Property 11: 车次类型识别** - 验证车次类型正确识别
    - _Requirements: 3.5, 4.5_
  
  - [ ]* 5.3 编写数据解析的单元测试
    - 测试具体的12306数据格式示例
    - 测试边界情况（空数据、格式错误）
    - _Requirements: 3.5_

- [x] 6. 实现TrainService核心逻辑
  - [x] 6.1 集成缓存到查询流程
    - 在query_trains中实现缓存检查逻辑
    - 实现_get_cached_result和_set_cached_result方法
    - 在响应中添加from_cache和query_time标志
    - _Requirements: 8.1, 8.2, 8.4_
  
  - [ ]* 6.2 编写缓存集成的属性测试
    - **Property 20: 缓存响应标注** - 验证缓存响应包含标志和时间戳
    - _Requirements: 8.4_
  
  - [x] 6.3 实现站点选择和保存
    - 实现save_selected_station方法
    - 实现get_selected_stations方法
    - _Requirements: 1.3_
  
  - [ ]* 6.4 编写站点选择的属性测试
    - **Property 3: 站点选择持久化** - 验证选择的站点被正确保存
    - _Requirements: 1.3_

- [ ] 7. Checkpoint - 确保后端核心功能测试通过
  - 运行所有后端测试
  - 确保TrainService的所有方法正常工作
  - 如有问题请询问用户

- [x] 8. 实现API路由和验证
  - [x] 8.1 实现车站搜索API端点
    - 实现GET /api/train/stations端点
    - 添加参数验证（keyword最小长度1）
    - 实现依赖注入get_train_service
    - _Requirements: 1.1, 9.1, 9.2_
  
  - [x] 8.2 实现车次查询API端点
    - 实现GET /api/train/query端点
    - 添加参数验证（from_station, to_station, date）
    - 实现日期范围验证（当前日期起30天内）
    - _Requirements: 2.2, 3.1, 9.1, 9.2_
  
  - [ ]* 8.3 编写日期验证的属性测试
    - **Property 4: 日期验证规则** - 验证接受30天内日期并拒绝其他日期
    - _Requirements: 2.2_
  
  - [x] 8.4 实现刷新查询API端点
    - 实现GET /api/train/refresh端点绕过缓存
    - 复用query_trains逻辑但跳过缓存检查
    - _Requirements: 5.5, 8.5_
  
  - [ ]* 8.5 编写API端点的属性测试
    - **Property 21: JSON请求解析** - 验证有效JSON请求被正确解析
    - **Property 22: JSON响应格式** - 验证响应是有效JSON且包含trains列表
    - **Property 23: API响应结构一致性** - 验证所有响应包含状态码和错误信息
    - _Requirements: 9.2, 9.3, 9.5_

- [x] 9. 实现错误处理
  - [x] 9.1 创建自定义异常类
    - 在app/core/exceptions.py中添加NetworkError、API12306Error、DataParseError、ValidationError
    - 实现异常的错误码和消息
    - _Requirements: 7.1, 7.2, 7.3_
  
  - [x] 9.2 实现全局异常处理器
    - 在app/main.py中添加异常处理中间件
    - 实现统一的ErrorResponse格式
    - 处理所有自定义异常类型
    - _Requirements: 7.1, 7.2, 7.3, 9.5_
  
  - [ ]* 9.3 编写错误处理的属性测试
    - **Property 7: 错误处理完整性** - 验证所有错误场景都有提示
    - _Requirements: 3.3, 7.2, 7.3_
  
  - [ ]* 9.4 编写错误处理的单元测试
    - 测试网络连接失败场景
    - 测试查询超时场景
    - 测试参数不完整场景
    - _Requirements: 7.1, 7.3, 7.4_

- [x] 10. 实现查询历史功能
  - [x] 10.1 实现查询历史保存
    - 在TrainService中实现save_query_history方法
    - 实现最多保存10条的逻辑
    - 使用数据库或本地存储
    - _Requirements: 6.1, 6.2_
  
  - [ ]* 10.2 编写查询历史的属性测试
    - **Property 13: 查询历史保存** - 验证查询被保存
    - **Property 14: 历史记录数量限制** - 验证只保留最近10条
    - _Requirements: 6.1, 6.2_
  
  - [x] 10.3 实现查询历史查询API
    - 实现GET /api/train/history端点
    - 返回用户的查询历史列表
    - _Requirements: 6.3_
  
  - [ ]* 10.4 编写历史查询的属性测试
    - **Property 15: 历史记录显示完整性** - 验证历史记录包含所有字段
    - _Requirements: 6.3_

- [ ] 11. Checkpoint - 确保后端API测试通过
  - 运行所有后端测试
  - 使用Postman或curl测试所有API端点
  - 如有问题请询问用户

- [x] 12. 实现前端查询表单组件
  - [x] 12.1 创建StationSelector组件
    - 在frontend/src/components/train/StationSelector.vue中创建组件
    - 实现站点搜索输入框
    - 实现搜索结果下拉列表
    - 实现防抖搜索
    - _Requirements: 1.1, 1.2_
  
  - [x] 12.2 创建DatePicker组件
    - 在frontend/src/components/train/DatePicker.vue中创建组件
    - 使用原生日期选择器或第三方库
    - 限制日期范围（今天到30天后）
    - _Requirements: 2.1, 2.2_
  
  - [x] 12.3 创建查询表单
    - 在frontend/src/views/TrainQueryView.vue中创建主视图
    - 集成StationSelector和DatePicker
    - 实现查询按钮和加载状态
    - _Requirements: 1.1, 2.1, 3.1_

- [x] 13. 实现前端查询逻辑
  - [x] 13.1 创建useTrainQuery组合式函数
    - 在frontend/src/composables/useTrainQuery.js中创建
    - 实现queryTrains方法调用后端API
    - 实现refreshQuery方法绕过缓存
    - 管理loading和error状态
    - _Requirements: 3.1, 5.5_
  
  - [x] 13.2 实现查询历史保存
    - 在useTrainQuery中实现saveQueryHistory方法
    - 使用localStorage保存历史
    - 实现最多10条的限制
    - _Requirements: 6.1, 6.2_
  
  - [ ]* 13.3 编写前端查询逻辑的单元测试
    - 测试queryTrains方法
    - 测试历史保存逻辑
    - 使用Vitest进行测试
    - _Requirements: 3.1, 6.1_

- [x] 14. 实现前端结果展示组件
  - [x] 14.1 创建TrainList组件
    - 在frontend/src/components/train/TrainList.vue中创建
    - 显示车次列表
    - 实现加载状态和空状态
    - 实现刷新按钮
    - _Requirements: 4.1, 4.2, 5.5_
  
  - [x] 14.2 创建TrainItem组件
    - 在frontend/src/components/train/TrainItem.vue中创建
    - 显示单个车次的详细信息
    - 显示车次号、时间、时长
    - 显示所有座位类型和余票
    - 实现余票的格式化显示（有/无）
    - _Requirements: 4.1, 4.2, 5.1, 5.2, 5.3_
  
  - [ ]* 14.3 编写结果展示的属性测试
    - **Property 9: 车次信息显示完整性** - 验证显示包含所有必需信息
    - **Property 12: 余票显示格式** - 验证余票格式正确
    - _Requirements: 4.1, 4.2, 5.1, 5.2, 5.3_

- [x] 15. 实现车次排序和过滤
  - [x] 15.1 实现车次排序功能
    - 在TrainList组件中实现排序逻辑
    - 默认按出发时间升序排序
    - 可选按时长、票价排序
    - _Requirements: 4.4_
  
  - [ ]* 15.2 编写排序的属性测试
    - **Property 10: 车次排序不变性** - 验证排序后按时间升序
    - _Requirements: 4.4_
  
  - [x] 15.3 实现车次类型过滤
    - 添加车次类型筛选器（高铁/动车/普通）
    - 根据车次号首字母识别类型
    - _Requirements: 4.5_

- [x] 16. 实现查询历史组件
  - [x] 16.1 创建QueryHistory组件
    - 在frontend/src/components/train/QueryHistory.vue中创建
    - 显示最近10条查询历史
    - 实现点击历史记录填充表单
    - 实现清除历史功能
    - _Requirements: 6.3, 6.4, 6.5_
  
  - [ ]* 16.2 编写历史组件的属性测试
    - **Property 16: 历史记录回填** - 验证点击历史记录填充表单
    - _Requirements: 6.4_

- [x] 17. 实现前端错误处理
  - [x] 17.1 创建错误处理工具
    - 在frontend/src/utils/errorHandler.js中创建handleTrainError函数
    - 根据错误类型显示不同提示
    - 集成到useTrainQuery中
    - _Requirements: 7.1, 7.2, 7.3, 7.4_
  
  - [x] 17.2 创建通知组件
    - 创建Toast或Notification组件显示错误
    - 支持不同类型（error/warning/info）
    - _Requirements: 7.1, 7.2, 7.3_

- [x] 18. 添加路由和导航
  - [x] 18.1 配置前端路由
    - 在frontend/src/router/index.js中添加/train路由
    - 配置TrainQueryView为路由组件
    - _Requirements: 9.1_
  
  - [x] 18.2 添加导航链接
    - 在Header组件中添加"火车票查询"导航链接
    - _Requirements: 9.1_

- [x] 19. 样式和用户体验优化
  - [x] 19.1 实现响应式布局
    - 确保在移动设备上正常显示
    - 使用CSS Grid或Flexbox布局
    - _Requirements: 4.1, 4.2_
  
  - [x] 19.2 添加加载动画
    - 在查询时显示加载动画
    - 使用LoadingSpinner组件
    - _Requirements: 3.1_
  
  - [x] 19.3 优化交互体验
    - 添加输入验证提示
    - 添加成功查询的反馈
    - 优化按钮状态和禁用逻辑
    - _Requirements: 2.2, 7.3_

- [ ] 20. Final Checkpoint - 端到端测试
  - 启动后端和前端服务
  - 测试完整的查询流程
  - 测试缓存功能
  - 测试查询历史
  - 测试错误处理
  - 测试所有边界情况
  - 如有问题请询问用户

- [ ]* 21. 集成测试
  - [ ]* 21.1 编写前后端集成测试
    - 测试完整的查询流程
    - 测试缓存机制
    - 测试错误处理流程
    - _Requirements: 3.1, 8.1, 8.2_

- [ ]* 22. 性能测试
  - [ ]* 22.1 测试并发查询
    - 使用locust或类似工具进行负载测试
    - 验证系统在高负载下的表现
    - _Requirements: 10.4_
  
  - [ ]* 22.2 测试缓存性能
    - 验证缓存命中率
    - 测试缓存对响应时间的影响
    - _Requirements: 10.5_

## Notes

- 标记为`*`的任务是可选的，可以跳过以加快MVP开发
- 每个任务都引用了具体的需求编号以便追溯
- Checkpoint任务确保增量验证
- 属性测试验证通用正确性属性
- 单元测试验证特定示例和边界情况
- 建议按顺序执行任务，因为后面的任务依赖前面的任务
- 12306 API可能需要特殊处理（如Cookie、请求头），实施时需要根据实际情况调整
