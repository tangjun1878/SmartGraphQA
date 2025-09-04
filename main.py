

#****************************************************************调用嵌入embed模型与语言LLM模型****************************************************************#
from Models.Embed_Models import EmbeddingsModels
emd_model = EmbeddingsModels()

from Models.LLM_Models import build_model,invoke, stream_invoke
llm_model = build_model(mode="qwen3_14b")





from typing import Dict, List
from prompts123.graph_prompt import graph_extraction, graph_extraction_parameter_default
from Models.LLM_Models import build_model, stream_invoke,remove_think
import os
from DataBase.config import neo4j_config





def build_prompt(text, entity_types=None) :
    """构建完整的提示词"""
    params = graph_extraction_parameter_default
    params['input_text'] = text
    if entity_types is not None:
        params['entity_types']=entity_types

    return graph_extraction.format(**params)


def read_file(file_path: str) -> str:
    """读取TXT文件内容"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"❌ 文件未找到：{file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        
        return f.read().strip()

import re

def split_text_by_newline(text: str) -> list:
    """
    将文本按换行符分割，每个非空行作为一个列表元素。
    
    :param text: 原始文本（字符串）
    :return: 分割后的非空行列表
    """
    return [line.strip() for line in text.splitlines() if line.strip()]


from DataBase.GraphData.create_graph_knowledge import  TripleDataParser, Neo4jGraphData
from prompts123.graph_prompt import TUPLE_DELIMITER,RECORD_DELIMITER,COMPLETION_DELIMITER,system_prompt

dataparse = TripleDataParser(TUPLE_DELIMITER,RECORD_DELIMITER,COMPLETION_DELIMITER)

from DataBase.config import neo4j_config



uri, user, password, database = neo4j_config['uri'],neo4j_config['user'],neo4j_config['password'],neo4j_config['database']
graph = Neo4jGraphData(uri, user, password, database)

from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage





def extract_and_write_graph_data(graph_class,entity_types,text_lst,system_prompt,batch):
     # Step 3: 使用 ChatPromptTemplate 构建完整提示
    chat_template = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{user_input}"),
    ])

    for i,t in enumerate(text_lst):
        prompt = build_prompt(t,entity_types=entity_types)

        formatted_messages = chat_template.format_messages(user_input=prompt)
        response = stream_invoke(llm_model,formatted_messages)
        response = remove_think(response)

        extract_graph_text = {"graph_text":response,"textid":str(i) }

     
        entities, relationships = dataparse.batch_parse_data(extract_graph_text, batch=batch)
        graph_class.write_entities_and_relationships(entities, relationships)

    if dataparse._buffer:
        entities, relationships = dataparse.flush()
        graph_class.write_entities_and_relationships(entities, relationships)


def write_graph_demo():
    text_file = read_file('/extend_disk/disk3/tj/langchain/SmartGraphQA-master/report_year.txt')
    text_lst = split_text_by_newline(text_file)
    entity_types="组织、人物、日期、文件"
    batch = 2

    extract_and_write_graph_data(graph,entity_types,text_lst,system_prompt,batch)
    graph.close() # 关闭数据库连接






if __name__ == "__main__":
    
    
    
    write_graph_demo()















































































































