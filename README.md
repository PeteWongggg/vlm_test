# vlm_test

## 配置

所有推理及页面参数集中在 `config/config.yaml`；可修改模型名称、私有化接口地址、API Key、提示词、采样参数及允许的图片类型，无需改动代码。

## 前端演示服务

```bash
pip install -r requirements.txt
python run.py --reload
```

访问 `http://localhost:8000` 上传 PNG/JPEG/SVG 图片并查看生成结果与 token 统计；可通过 `--host`、`--port` 自定义监听地址。