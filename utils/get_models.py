import requests
import json

def get_openrouter_models():
    """
    查询OpenRouter API获取所有支持的模型
    """
    url = "https://openrouter.ai/api/v1/models"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")
        return None

def filter_multimodal_models(models_data):
    """
    筛选出支持多模态（图像输入）的模型
    """
    if not models_data or 'data' not in models_data:
        return []
    
    multimodal_models = []
    
    for model in models_data['data']:
        # 检查模型是否支持图像输入
        architecture = model.get('architecture', {})
        modality = architecture.get('modality', '')
        
        # 检查多种可能的多模态标识
        is_multimodal = (
            'vision' in modality.lower() or
            'image' in modality.lower() or
            'multimodal' in modality.lower() or
            'vision' in model.get('id', '').lower()
        )
        
        if is_multimodal:
            multimodal_models.append({
                'id': model.get('id', 'N/A'),
                'name': model.get('name', 'N/A'),
                'description': model.get('description', 'N/A'),
                'context_length': model.get('context_length', 'N/A'),
                'pricing': model.get('pricing', {}),
                'modality': modality
            })
    
    return multimodal_models

def display_models(models, output_format='text'):
    """
    显示模型列表
    output_format: 'text', 'json', 'csv'
    """
    if not models:
        print("未找到多模态模型")
        return
    
    print(f"\n找到 {len(models)} 个多模态模型:\n")
    print("=" * 100)
    
    if output_format == 'json':
        print(json.dumps(models, indent=2, ensure_ascii=False))
    
    elif output_format == 'csv':
        print("ID,Name,Context Length,Prompt Price,Completion Price")
        for model in models:
            pricing = model.get('pricing', {})
            prompt_price = pricing.get('prompt', 'N/A')
            completion_price = pricing.get('completion', 'N/A')
            print(f"{model['id']},{model['name']},{model['context_length']},{prompt_price},{completion_price}")
    
    else:  # text format
        for i, model in enumerate(models, 1):
            print(f"\n{i}. {model['name']}")
            print(f"   ID: {model['id']}")
            print(f"   描述: {model['description'][:100]}..." if len(model['description']) > 100 else f"   描述: {model['description']}")
            print(f"   上下文长度: {model['context_length']}")
            
            pricing = model.get('pricing', {})
            if pricing:
                prompt_price = pricing.get('prompt', 'N/A')
                completion_price = pricing.get('completion', 'N/A')
                print(f"   价格 - Prompt: ${prompt_price}/token, Completion: ${completion_price}/token")
            
            print(f"   模态: {model['modality']}")
            print("-" * 100)

def save_to_file(models, filename='multimodal_models.json'):
    """
    将结果保存到文件
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(models, f, indent=2, ensure_ascii=False)
        print(f"\n结果已保存到: {filename}")
    except Exception as e:
        print(f"保存文件失败: {e}")

def main():
    print("正在查询 OpenRouter 多模态模型...")
    
    # 获取所有模型
    models_data = get_openrouter_models()
    
    if not models_data:
        return
    
    # 筛选多模态模型
    multimodal_models = filter_multimodal_models(models_data)
    
    # 显示结果
    display_models(multimodal_models, output_format='text')
    
    # 可选：保存到文件
    save_choice = input("\n是否保存结果到JSON文件? (y/n): ").lower()
    if save_choice == 'y':
        save_to_file(multimodal_models)
    
    # 可选：导出CSV
    csv_choice = input("是否导出为CSV格式? (y/n): ").lower()
    if csv_choice == 'y':
        print("\n--- CSV格式 ---")
        display_models(multimodal_models, output_format='csv')

if __name__ == "__main__":
    main()