import base64
# from langchain.chat_models import ChatOpenAI
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage




mllm_config = {
    "qwen2.5vl_32b": {
        "model_name": "qwen2.5vl:32b",
        "api_url": "http://192.168.10.22:6542/v1",
        "api_key": "sk-RJaJE4fXaktHAI2MB295F6Ad58004f7eBcE255B863CdD6F0",
        "max_tokens": 20000,
        "temperature": 0.1,  # 越低越稳定
    },
     "qwen2.5vl_72b": {
        "model_name": "qwen2.5vl:72b",
        "api_url": "http://192.168.10.22:6542/v1",
        "api_key": "sk-RJaJE4fXaktHAI2MB295F6Ad58004f7eBcE255B863CdD6F0",
        "max_tokens": 20000,
        "temperature": 0.1,  # 越低越稳定
    }
}






def build_mllm_model(mode="qwen2.5vl_32b"):
    config = mllm_config[mode]
    model_name = config["model_name"]
    api_key = config["api_key"]    
    api_url = config["api_url"]
    temperature = config["temperature"]
    max_tokens = config["max_tokens"]
    MLLM = ChatOpenAI(
        model=model_name,
        openai_api_key=api_key,
        openai_api_base=api_url,
        temperature=temperature,
        max_tokens=max_tokens
    )
    return MLLM






def load_image(image_path):
    """优化图像预处理流程"""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode('utf-8')

def get_prompt_vl(prompt, system_prompt=None,image=None,image_path=None):
    """
    构建多模态prompt
    :param prompt: 用户指令
    :param system_prompt: 系统提示
    :param image: 图片数据,为base64编码格式
    :param image_path: 图片路径
    image与image_path二选一,必须有一个有值。
    
    """
    
    
    messages=[]
    if system_prompt:
        messages.append( SystemMessage(content=system_prompt)) 
    if image or image_path:    # 构建多模态消息
        
        image_base64 = image if image else load_image(image_path)

        human_prompt = HumanMessage(
                content=[
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}",
                            "detail": "high"  # 增强图像识别精度
                        }
                    }
                ]
            )
    else:

        human_prompt = HumanMessage( content= prompt   )
    messages.append(human_prompt)
       
    return messages


def stream_invoke_vl(llm_model, messages):
    """优化流式输出处理器"""
    full_response = ""
    for chunk in llm_model.stream(messages):
        # 实时处理特殊符号转义
        processed_content = chunk.content.replace(")GB/T", ") GB/T")  # 修复示例中的格式错误
        print(processed_content, end="", flush=True)
        full_response += processed_content
    return full_response





def infer_vl(model,prompt,system_prompt=None,image=None,image_path=None):
    messages = get_prompt_vl(prompt, system_prompt=system_prompt,image=image,image_path=image_path)
    # 执行转换
    response = stream_invoke_vl(model, messages)

    return response


if __name__ == "__main__":

    system_prompt="""你是一个图片内容提取助手，请根据用户指令提取图片中的内容。整个过程需要严格保持以下要求：\n
            如果是英文内容必须翻译成中文。\n
            输出结果必须是中文和markdown格式。"""

    prompt = "请描述图像内容"
    image_path = "/extend_disk/d2/tj/langchain/SmartGraphQA-master/Models/1.jpg"
    model = build_mllm_model(mode="qwen2.5vl_32b")
    response = infer_vl(model,prompt,system_prompt=system_prompt,image_path=image_path)
    print(response)








