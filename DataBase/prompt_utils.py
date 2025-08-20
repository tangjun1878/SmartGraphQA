

from prompts123.graph_prompt import graph_extraction, graph_extraction_parameter_default
from langchain.schema import HumanMessage, SystemMessage



def build_prompt(text, entity_types=None) :
    """构建完整的提示词"""
    params = graph_extraction_parameter_default
    params['input_text'] = text
    if entity_types is not None:
        params['entity_types']=entity_types

    return graph_extraction.format(**params)





def build_graph_prompt(text, entity_types=None,system_prompt=None,extract_parameters=None) :
    """构建默认的知识图谱三元组关系"""
    
    params = graph_extraction_parameter_default
    if extract_parameters is not None:
        if set(extract_parameters.keys()) != set(graph_extraction_parameter_default.keys()):
            raise ValueError(f"extract_parameters 的键必须完全匹配：{list(graph_extraction_parameter_default.keys())}")
        params = extract_parameters  # 重新赋值

    params['input_text'] = text
    if entity_types is not None: # 存在就替换
        params['entity_types']=entity_types
    user_prompt = graph_extraction.format(**params)
    messages = []
    if system_prompt is not None:
        messages.append( SystemMessage(content=system_prompt)     )
    messages.append(HumanMessage(content=user_prompt))
    return messages









