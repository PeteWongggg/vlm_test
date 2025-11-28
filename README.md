# vlm_test

## 前端演示服务

多模态图生文服务，支持本地部署的 VLM 模型和通过 OpenRouter 访问其他 VLM 模型。

### 快速开始

```bash
pip install -r requirements.txt
python run.py --reload
```

访问 `http://localhost:8000` 上传 PNG/JPEG/SVG 图片并查看生成结果与 token 统计；可通过 `--host`、`--port` 自定义监听地址。

### 功能特性

- **本地模型支持**：支持调用本地部署的 VLM 模型（如 Qwen3-VL-8B-Instruct）
- **OpenRouter 集成**：可选择通过 OpenRouter 访问多个 VLM 模型：
  - Google Gemini Pro Vision
  - Claude 3 (Opus/Sonnet/Haiku)
  - GPT-4 Vision
  - Qwen VL Plus/Max
  - 更多模型可在配置中添加

### 配置说明

所有配置集中在 `config/config.yaml`：

- **本地模型配置**：`model` 节点配置本地模型的名称、接口地址、API Key 等
- **OpenRouter 配置**：`openrouter` 节点配置 OpenRouter API Key 和可用模型列表
  - 设置 `enabled: true` 启用 OpenRouter
  - 在 `api_key` 中填入你的 OpenRouter API Key
  - 在 `models` 列表中添加或移除支持的模型

修改配置后重启服务即可生效。