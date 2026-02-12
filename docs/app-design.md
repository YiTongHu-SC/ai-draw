# app-design PRD

## 1. 背景与目标

ai-draw 是一个本地可运行的命令行工具，调用 GPTSAPI 的图像生成接口，完成文生图或图生图的“最小可用”体验。目标是让新用户在 1-2 分钟内完成第一次出图，并支持常见配置（API Key、模型选择、输出格式等）。

核心目标：

- 极简易用：命令清晰、少参数即可出图。
- 本地可用：无需服务端部署，Python + Pipenv 即可运行。
- 可配置：支持 API Key、模型、出图格式与比例等配置。
- 智能模式：默认文生图；当用户上传本地文件时自动切换图生图。

## 2. 用户画像与使用场景

目标用户：

- 需要快速生成参考图的设计师、产品经理、开发者。
- 希望用脚本批量出图的工程用户。

典型场景：

- 输入一句提示词即可生成 PNG 图片。
- 选择指定模型进行同风格或更高质量出图。
- 上传本地图片，进行图生图（风格迁移、加强细节等）。

## 3. 范围与非范围

范围：

- CLI 交互与参数设计。
- 文生图 / 图生图能力。
- API Key 与模型配置。
- 生成结果保存到本地。

非范围：

- Web UI / GUI。
- 用户账号体系、云端图库。
- 高级图像编辑（抠图、局部重绘）。

## 4. 产品需求与功能清单

### 4.1 基本流程

1. 用户输入 prompt。
2. 选择模型、输出格式、输出路径等参数（可选）。
3. 调用 GPTSAPI 文生图接口创建任务。
4. 轮询任务结果并保存图片到本地。

### 4.2 文生图（默认）

- 当未传入本地图片路径时，使用文生图。
- 必选参数：prompt。
- 可选参数：模型、比例、格式、输出路径、超时与轮询间隔。

### 4.3 图生图（自动切换）

- 当用户传入本地图片路径时，自动使用图生图模式。
- 仍使用 prompt 作为引导。
- 若模型不支持图生图，需要清晰提示错误。

### 4.4 配置能力

- API Key：从环境变量 `GPTSAPI_API_KEY` 读取。
- 模型选择：通过 `--model` 指定。
- 供应商选择：通过 `--provider` 指定，默认 `google`。
- 输出参数：`--aspect`、`--format`、`--out`。
- 运行参数：`--timeout`、`--poll-interval`、`--verbose`。

## 5. CLI 设计（建议与对齐 README）

基础命令：

```bash
pipenv run python main.py "Generate a desert sunset image" --out demo.png
```

高级参数：

```bash
pipenv run python main.py "A neon city at night" \
	--provider google \
	--model gemini-2.5-flash-image \
	--aspect 1:1 \
	--format png \
	--out output.png \
	--poll-interval 2 \
	--timeout 120 \
	--verbose
```

图生图示例（建议，若参数已支持）：

```bash
pipenv run python main.py "保持绘画风格，优化细节" \
	--image ./prompt_img/frog.png \
	--out ./output/frog_v2.png
```

## 6. 交互与可用性要求

- 命令行提示清晰：缺少 `GPTSAPI_API_KEY` 时给出可读错误。
- 参数默认值合理：默认文生图、默认模型、默认输出 PNG。
- 输出路径不存在时自动创建目录（若可行）。
- 失败重试与错误提示：超时、模型不可用、API 请求失败。

## 7. 配置与默认值（建议）

- `provider`: google
- `model`: gemini-2.5-flash-image
- `aspect`: 1:1
- `format`: png
- `poll-interval`: 2 秒
- `timeout`: 120 秒

## 8. 质量与稳定性

- API 失败需返回明确错误码与提示。
- 轮询超时需要终止并返回失败原因。
- 写入文件失败时提示路径与权限。

## 9. 里程碑（建议）

1. CLI 基础流程可用（文生图）。
2. 自动切换图生图模式。
3. 错误处理与日志完善。

## 10. 打开问题

- 是否需要支持配置文件（如 `.env` 或 `config.json`）？
- 是否需要模型能力列表与自动校验？
- 是否需要输出元数据（如生成时间、模型、prompt）？
