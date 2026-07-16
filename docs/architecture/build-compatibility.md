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

Python 版本的唯一机器源是仓库根目录 `.python-version`；CI 和 Pages workflow
必须通过 `actions/setup-python` 的 `python-version-file` 读取它，不能再各自硬编码
版本。直接依赖维护在 `requirements.in`，完整传递依赖及哈希维护在
`requirements.lock`。安装后必须立即检查依赖图：

```bash
python -m pip install --require-hashes -r requirements.lock
python -m pip check
```

`tools/check_workflow_policy.py` 会同时拒绝 Python 版本双源、可跳过的 setup、
非 hash-locked 安装、缺失或可跳过的 `pip check`，并要求它们发生在 trust
校验之前。

`IOT-T063` / `IOT-F038` 进一步把 active-goal 合同提升为两套 workflow 的
显式 fail-closed 门禁。CI 与 Pages 必须在上述 bootstrap 完成后、inventory、
trust、tests 和 build 之前，各自恰好一次运行：

```bash
python tools/check_active_goal.py
```

workflow policy 会拒绝该命令缺失、重复、换序、嵌入 wrapper，或带有 `if`、
`continue-on-error`、`env`、`working-directory`、自定义 `shell` 的 step。

## 升级规则

1. 在独立分支更新 `requirements.in` 并重新生成锁文件。
2. 从空环境安装锁文件，运行单元测试、内容门禁和 `mkdocs build --strict`。
3. 检查首页、搜索、移动端与暗色模式，再合入依赖升级。
4. 不直接把生产构建切换到 MkDocs 2；兼容性尚未在本仓库验证，当前状态为 `UNKNOWN`。

锁文件保证“安装了什么”可追溯，但不能代替人工浏览器验收。
