from openai import OpenAI
import base64
import mimetypes
import datetime

model_name = "Qwen3-VL-8B-Instruct"
base_url = "http://localhost:8500/v1"
api_key = ""
prompt = "请根据提供的网页设计图，编写对应的HTML代码，将结果写在一个 markdown HTML 代码块中"
image_path = "image.png"

def image2base64(image_path: str) -> str:
    mime_type, _ = mimetypes.guess_type(image_path)
    if mime_type is None:
        mime_type = "image/png"

    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()

    return f"data:{mime_type};base64,{b64}"

messages = [
    {
        "role": "user",
        "content": [
            {"type": "text", "text": prompt},
            {
                "type": "image_url",
                "image_url": {
                    "url": image2base64(image_path)
                }
            }
        ]
    }
]

client = OpenAI(
    base_url=base_url,
    api_key=api_key
)

sampling_args = {
    "temperature": 0.7,
    "top_p": 0.8,
    "presence_penalty": 1.5,
    "max_completion_tokens": 16384,
    "top_k": 20,
    "repetition_penalty": 1.0,
}

extra_args = {}
if sampling_args.__contains__("top_k"):
    extra_args["top_k"] = sampling_args.pop("top_k")
if sampling_args.__contains__("repetition_penalty"):
    extra_args["repetition_penalty"] = sampling_args.pop("repetition_penalty")

start_at = datetime.datetime.now()
response = client.chat.completions.create(
    model=model_name,
    messages=messages,
    **sampling_args,
    extra_body=extra_args
)
end_at = datetime.datetime.now()

content = response.choices[0].message.content
usage = response.usage.to_dict()
seconds = (end_at - start_at).total_seconds()

print("=== Response ===")
print(content)
