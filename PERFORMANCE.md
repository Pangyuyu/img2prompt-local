# 性能分析与数据库迁移指南

## 📊 JSON 文件数量与性能关系

### 当前架构性能评估

#### 1. **文件数量与性能**

| JSON 文件数量 | 加载时间 | 内存占用 | 性能影响 | 建议 |
|--------------|----------|----------|----------|------|
| **< 100** | < 1 秒 | < 10MB | ✅ 无影响 | 继续使用 JSON |
| **100-500** | 1-3 秒 | 10-50MB | ✅ 轻微 | 可继续使用 JSON |
| **500-1000** | 3-5 秒 | 50-100MB | ⚠️ 开始变慢 | 考虑迁移数据库 |
| **1000-5000** | 5-15 秒 | 100-500MB | ❌ 明显卡顿 | 强烈建议数据库 |
| **> 5000** | > 15 秒 | > 500MB | ❌ 严重影响 | 必须数据库 |

#### 2. **性能瓶颈分析**

**当前 JSON 方案的瓶颈**：

```python
# 1. 加载所有 JSON 文件列表
for json_file in output_dir.glob("*.json"):  # O(n)
    data = json.load(open(json_file))        # O(n) × 文件大小
```

**时间复杂度**：O(n²) - 文件数量增加时，加载时间呈平方增长

**内存消耗**：每个 JSON 约 1-2KB，1000 个文件约 1-2MB（纯数据），但加载和解析过程会消耗更多内存

---

### 3. **实际使用场景估算**

#### 场景 A：个人用户
```
每天处理：50 张图片
每月处理：1,500 张图片
每年积累：18,000 张图片

建议：
- 0-6 个月（< 1000 张）：JSON 方案 ✅
- 6-12 个月（1000-5000 张）：建议迁移数据库 ⚠️
- 1 年以上（> 5000 张）：必须数据库 ❌
```

#### 场景 B：摄影工作室
```
每天处理：200 张图片
每月处理：6,000 张图片
每年积累：72,000 张图片

建议：
- 立即使用数据库（< 1 个月就超过 1000 张）
```

#### 场景 C：电商/自媒体
```
每天处理：500 张图片
每月处理：15,000 张图片

建议：
- 必须数据库 + 分布式存储
```

---

## 🗄️ 数据库迁移方案

### 推荐：SQLite

**优势**：
- ✅ 单文件，无需服务器
- ✅ 支持 SQL 查询
- ✅ 支持索引，查询快
- ✅ Python 内置支持
- ✅ 适合 1 万 -100 万条记录

**表结构设计**：

```sql
CREATE TABLE images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    md5 TEXT UNIQUE NOT NULL,
    source_path TEXT NOT NULL,
    original_filename TEXT,
    width INTEGER,
    height INTEGER,
    size_bytes INTEGER,
    format TEXT,
    description TEXT,
    positive_prompt TEXT,
    negative_prompt TEXT,
    compressed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    image_md5 TEXT NOT NULL,
    tag TEXT NOT NULL,
    tag_type TEXT DEFAULT 'cn',  -- 'cn' 中文 / 'en' 英文
    FOREIGN KEY (image_md5) REFERENCES images(md5)
);

-- 创建索引加速查询
CREATE INDEX idx_md5 ON images(md5);
CREATE INDEX idx_tags ON tags(tag);
CREATE INDEX idx_created ON images(created_at);
```

---

### 迁移时机判断

**当满足以下任一条件时，建议迁移到数据库**：

1. **文件数量** > 1000 个 JSON
2. **加载时间** > 5 秒
3. **内存占用** > 200MB
4. **用户反馈** 卡顿
5. **需要复杂查询**（按 tag 筛选、日期范围等）

---

### 迁移策略

#### 方案 1：渐进式迁移（推荐）

```python
# 1. 保持 JSON 存储不变
# 2. 添加数据库作为查询层
# 3. 新文件同时写入 JSON 和数据库
# 4. 后台任务逐步导入旧 JSON 到数据库
# 5. 查询时优先查数据库
```

#### 方案 2：一次性迁移

```python
# 1. 开发迁移工具
# 2. 用户手动触发迁移
# 3. 迁移完成后切换到数据库模式
# 4. 保留 JSON 作为备份
```

---

## 📈 优化建议

### 短期优化（JSON 方案）

1. **延迟加载**：
   - 只加载当前页需要的 JSON
   - 滚动加载更多

2. **缓存机制**：
   - 缓存已加载的 JSON 数据
   - 使用 LRU 缓存策略

3. **分页显示**：
   - 每页显示 50-100 条
   - 避免一次性加载全部

4. **异步加载**：
   - 后台线程加载 JSON
   - 不阻塞 UI

### 长期优化（数据库方案）

1. **SQLite + 全文搜索**：
   - 支持 tag 快速筛选
   - 支持描述全文搜索

2. **定期归档**：
   - 按月份归档旧数据
   - 保持活跃数据在 1000 条以内

3. **混合存储**：
   - 最近 100 条：JSON（快速访问）
   - 历史数据：数据库（长期存储）

---

## 🎯 结论

**对于当前项目**：

| 用户类型 | 建议 |
|----------|------|
| 个人用户（< 500 张/月） | JSON 方案可用 6-12 个月 |
| 重度用户（500-2000 张/月） | 3 个月后考虑数据库 |
| 商业用户（> 2000 张/月） | 立即使用数据库 |

**推荐阈值**：
- **1000 个 JSON 文件**：性能拐点
- **5000 个 JSON 文件**：必须迁移

**监控指标**：
- 打开数据查看器的时间 > 3 秒
- 内存占用 > 200MB
- CPU 占用持续 > 50%

达到任一指标即触发迁移提醒。

---

*最后更新：2026-03-14*
