import os
import re
from typing import Dict, List

# LangChain相关导入
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage

# 自定义模块导入
from Prompts.prompt_graph import (
    graph_extraction, 
    graph_extraction_parameter_default,
    TUPLE_DELIMITER,
    RECORD_DELIMITER,
    COMPLETION_DELIMITER,
    system_prompt
)
from Models.LLM_Models import build_model, stream_invoke, remove_think
from DataBase.config import neo4j_config
from DataBase.GraphData.create_graph_knowledge import TripleDataParser, Neo4jGraphData

# 初始化LLM模型
llm_model = build_model(mode="qwen3_14b")

# 初始化图谱数据库连接
uri, user, password, database = (
    neo4j_config['uri'],
    neo4j_config['user'],
    neo4j_config['password'],
    neo4j_config['database']
)
graph = Neo4jGraphData(uri, user, password, database)
dataparse = TripleDataParser(
    TUPLE_DELIMITER,
    RECORD_DELIMITER,
    COMPLETION_DELIMITER
)


def build_prompt(text: str, entity_types: str = None) -> str:
    """
    构建完整的提示词
    
    :param text: 输入文本
    :param entity_types: 实体类型列表，如"组织、人物、日期、文件"
    :return: 格式化后的提示词
    """
    params = graph_extraction_parameter_default
    params['input_text'] = text
    
    if entity_types is not None:
        params['entity_types'] = entity_types
        
    return graph_extraction.format(**params)


def read_file(file_path: str) -> str:
    """
    读取TXT文件内容
    
    :param file_path: 文件路径
    :return: 文件内容字符串
    :raises FileNotFoundError: 当文件不存在时抛出异常
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"❌ 文件未找到：{file_path}")
        
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read().strip()


def split_text_by_newline(text: str) -> list:
    """
    将文本按换行符分割，每个非空行作为一个列表元素
    
    :param text: 原始文本（字符串）
    :return: 分割后的非空行列表
    """
    return [line.strip() for line in text.splitlines() if line.strip()]


def extract_and_write_graph_data(
    graph_class,
    entity_types: str,
    text_lst: list,
    system_prompt: str,
    batch: int
) -> None:
    """
    提取文本中的图谱数据并写入数据库
    
    :param graph_class: 图谱数据库操作类实例
    :param entity_types: 实体类型列表
    :param text_lst: 文本列表
    :param system_prompt: 系统提示词
    :param batch: 批量处理大小
    """
    # 构建聊天提示模板
    chat_template = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{user_input}"),
    ])

    for i, text in enumerate(text_lst):
        # 构建提示词并获取模型响应
        prompt = build_prompt(text, entity_types=entity_types)
        formatted_messages = chat_template.format_messages(user_input=prompt)
        response = stream_invoke(llm_model, formatted_messages)
        response = remove_think(response)

        # 解析并写入图谱数据
        extract_graph_text = {"graph_text": response, "textid": str(i)}
        entities, relationships = dataparse.batch_parse_data(
            extract_graph_text, 
            batch=batch
        )
        graph_class.write_entities_and_relationships(entities, relationships)

    # 处理缓冲区中剩余的数据
    if dataparse._buffer:
        entities, relationships = dataparse.flush()
        graph_class.write_entities_and_relationships(entities, relationships)


def write_graph_demo() -> None:
    """图谱数据写入示例函数"""
    # 配置参数
    text_file_path = '/extend_disk/disk3/tj/langchain/SmartGraphQA-master/DataBase/example_data.txt'
    entity_types = "组织、人物、文件"
    batch_size = 1

    # 执行流程
    text_file = read_file(text_file_path)
    text_lst = split_text_by_newline(text_file)
    
    extract_and_write_graph_data(
        graph, 
        entity_types, 
        text_lst, 
        system_prompt, 
        batch_size
    )
    
    # 关闭数据库连接
    graph.close()


if __name__ == "__main__":
    write_graph_demo()
