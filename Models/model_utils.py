




from Models.LLM_Models import build_model, invoke, stream_invoke,remove_think

# 语言模型回答的方法
def llm_generate(llm_model=None,prompt=None): 
    response='' # 给一个空字符，防止报错
    if llm_model is None or prompt is None:
        raise ValueError('请核对提取语言模型或提示是否存在有效值！')
    response = stream_invoke(llm_model,prompt)
    response = remove_think(response)
    return response




