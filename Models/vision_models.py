import base64
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage






# 配置多模态模型
mllm = ChatOpenAI(
    openai_api_key="sk-RJaJE4fXaktHAI2MB295F6Ad58004f7eBcE255B863CdD6F0",
    openai_api_base="http://192.168.10.22:6542/v1/",
    model_name="qwen2.5vl:72b",
    temperature=0.3,
    max_tokens=20000
)



system_prompt_default="""你是一个图片内容提取助手，请根据用户指令提取图片中的内容。整个过程需要严格保持以下要求：\n
            如果是英文内容必须翻译成中文。\n
            输出结果必须是中文和markdown格式。"""

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
    
    system_prompt_ = system_prompt_default if not system_prompt else system_prompt
    messages=[] 
    messages.append( SystemMessage(content=system_prompt_)) 
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



def infer_vl(prompt,system_prompt=None,image=None,image_path=None):
    messages = get_prompt_vl(prompt, system_prompt=system_prompt,image=image,image_path=image_path)
    # 执行转换
    response = stream_invoke_vl(mllm, messages)

    return response


if __name__ == "__main__":
    prompt = "请识别图像中的内容，保持图像原有的格式，只要求提取图像中的文字信息和表格，不要输出其他信息。输出格式为markdown格式。"
    image_path = "/extend_disk/disk3/tj/RagAgentDialogue/database/2.jpg"
    response = infer_vl(prompt,image_path=image_path)
    print(response)








