# 构建兼容性基线

本站把构建环境当作可审查的发布输入，而不是开发机上的偶然状态。

## 当前基线

| 组件 | 版本 / 策略 |
|---|---|
| Python | 3.11 |
| MkDocs | 1.6.1 |
| Material for MkDocs | 9.7.6 |
| PyMdown Extensions | 10.21.3 |
| PyYAML | 6.0.3 |
| jsonschema | 4.25.1 |

直接依赖维护在 `requirements.in`，完整传递依赖及哈希维护在
`requirements.lock`。CI 和 Pages 构建必须使用：

```bash
python -m pip install --require-hashes -r requirements.lock
```

## 升级规则

1. 在独立分支更新 `requirements.in` 并重新生成锁文件。
2. 从空环境安装锁文件，运行单元测试、内容门禁和 `mkdocs build --strict`。
3. 检查首页、搜索、移动端与暗色模式，再合入依赖升级。
4. 不直接把生产构建切换到 MkDocs 2；兼容性尚未在本仓库验证，当前状态为 `UNKNOWN`。

锁文件保证“安装了什么”可追溯，但不能代替人工浏览器验收。
