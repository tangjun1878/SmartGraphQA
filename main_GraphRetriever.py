from langchain.graphs import Neo4jGraph
from langchain.prompts import PromptTemplate
from typing import List, Dict, Tuple, Optional
from Models.LLM_Models import build_model
import networkx as nx
import matplotlib.pyplot as plt

from Models.model_utils import llm_generate
from DataBase.prompt_utils import build_graph_prompt
from DataBase.config import  neo4j_config, default_graph_config
from prompts123.graph_prompt import system_prompt

class KnowledgeGraphRetriever:
    '''知识图谱检索器，用于实体关系提取、查询和回答生成'''
    
    def __init__(self):
        """初始化知识图谱检索器，连接到Neo4j图数据库"""
        # 连接到Neo4j图数据库
        self.graph = Neo4jGraph(
            url=neo4j_config['uri'],
            username=neo4j_config['user'],
            password=neo4j_config['password'],
            database=neo4j_config['database']
        )
        
        self.default_graph_config = default_graph_config
        self.default_system_prompt = system_prompt  
    
    def generate_entity_relation(self, llm_model=None,
                                 input_text=None,
                                 entity_type=None,
                                 system_prompt=None,
                                 extract_parameters=None):
        """生成实体关系"""
        if extract_parameters is None:
            extract_parameters = self.default_graph_config
            
        prompt = build_graph_prompt(
            input_text, 
            entity_types=entity_type,
            system_prompt=system_prompt,
            extract_parameters=extract_parameters
        )
        
        if llm_model is None or input_text is None:
            raise ValueError('请提供有效的语言模型和输入文本！')

        response = llm_generate(llm_model=llm_model, prompt=prompt)
        return response

    def parse_from_generate_entity_relation(self, data):
        """解析实体关系字符串为实体列表和关系列表"""
        # 定义分隔符
        tuple_delimiter = self.default_graph_config['tuple_delimiter']
        record_delimiter = self.default_graph_config['record_delimiter']
        completion_delimiter = self.default_graph_config['completion_delimiter']

        # 清理数据：去除结尾的完成分隔符并分割记录
        cleaned_data = data.rstrip(completion_delimiter)
        records = cleaned_data.split(record_delimiter)

        entities = []
        relationships = []

        for record in records:
            record = record.strip()
            if not record:
                continue  # 跳过空行
                
            # 移除包围的括号
            if record.startswith(("(entity", "(relationship")):
                content = record[1:-1]  # 去掉开头的 ( 和结尾的 )
                parts = [part.strip() for part in content.split(tuple_delimiter)]
                
                if "entity" in record:
                    # 解析实体
                    entities.append({
                        "entity_name": parts[1].strip("'\""),
                        "entity_type": parts[2].strip("'\""),
                        "entity_description": parts[3].strip("'\"")
                    })
                elif "relationship" in record:
                    # 解析关系
                    relationships.append({
                        "source_entity": parts[1].strip("'\""),
                        "target_entity": parts[2].strip("'\""),
                        "relationship_description": parts[3].strip("'\""),
                        "relationship_strength": float(parts[4].strip("'\""))
                    })
        
        return entities, relationships


    def query2entity_relation(self, llm_model=None,
                              input_text=None,
                              entity_type=None,
                              system_prompt=None,
                              extract_parameters=None):
        '''提取实体和关系列表'''
        if llm_model is None or input_text is None:
            raise Exception('llm_model和input_text都必须有值，请核对！')
        

        data_response = self.generate_entity_relation(
            llm_model=llm_model,
            input_text=input_text,
            entity_type=entity_type,
            system_prompt=system_prompt if system_prompt is not None else self.default_system_prompt,
            extract_parameters=extract_parameters
        )
        
        entities, relationships = self.parse_from_generate_entity_relation(data_response)
        return entities, relationships
    

    


    def query_neo4j_by_entity(self, entity_name: str, max_depth: int = 1) -> List[Dict]:
        """
        查询给定实体的所有属性及指定深度内（≤max_depth）的关联实体和关系信息
        明确区分第一层（depth=1）和第二层（depth=2）等不同深度的内容
        
        :param entity_name: 要查询的实体名称
        :param max_depth: 最大查询深度，0表示只查自身，1表示直接关联（第一层），2表示包含第二层关联
        :return: 包含实体、关系属性及明确深度标记的字典列表
        """
        if not entity_name or max_depth < 0:
            return []

        # 构建支持可变深度的Cypher查询，确保能获取每层具体信息
        if max_depth == 0:
            cypher = """
            MATCH (n {name: $entity_name})
            RETURN properties(n) AS source_properties, 0 AS actual_depth
            """
        else:
            # 匹配1到max_depth层的所有路径，保留完整路径信息用于分层
            cypher = """
            MATCH path = (n {name: $entity_name})-[*1..%d]-(related)
            WITH 
                properties(n) AS source_properties,
                nodes(path) AS path_nodes,  // 路径上的所有节点（源节点+各级关联节点）
                relationships(path) AS path_rels,  // 路径上的所有关系
                length(path) AS actual_depth  // 实际路径长度（1表示第一层，2表示第二层）
            
            RETURN 
                source_properties,
                actual_depth,
                [node IN tail(path_nodes) | properties(node)] AS related_entities,  // 关联节点属性
                [rel IN path_rels | properties(rel)] AS relationships  // 关系属性
            """ % max_depth

        try:
            result = self.graph.query(cypher, params={"entity_name": entity_name})
            
            formatted_result = []
            for record in result:
                formatted = {
                    "source_entity": record["source_properties"],
                    "actual_depth": record["actual_depth"],
                    "layers": []  # 每个元素代表一层，明确标记depth
                }
                
                # 逐层处理，明确标记每层的深度（1开始）
                for layer_index in range(record["actual_depth"]):
                    # layer_index=0对应第一层（depth=1），layer_index=1对应第二层（depth=2）
                    formatted["layers"].append({
                        "depth": layer_index + 1,  # 明确标记当前是第几层
                        "relationship": record["relationships"][layer_index],  # 当前层的关系属性
                        "entity": record["related_entities"][layer_index]  # 当前层的关联实体属性
                    })
                
                formatted_result.append(formatted)
            
            return formatted_result
        except Exception as e:
            print(f"Neo4j查询错误: {str(e)}")
            return []


    def generate_answer(self, llm_model, question: str, entity_name: str, kg_info: List[Dict]) -> str:
        """
        优化后的回答生成方法：增加信息过滤和相关性排序
        
        参数:
            llm_model: 大语言模型
            question: 原始问题
            entity_name: 相关实体名称
            kg_info: 从知识图谱查询到的信息
            
        返回:
            生成的自然语言回答
        """
        if not kg_info:
            return f"未找到与实体「{entity_name}」相关的信息，无法回答问题。"
        
        # # 1. 提取问题关键词，用于过滤相关信息
        # question_keywords = self._extract_keywords(question)
        
        # # 2. 过滤并排序知识图谱信息（保留与问题关键词相关的内容）
        # filtered_kg_info = self._filter_kg_info(kg_info, question_keywords)
        
        # if not filtered_kg_info:
        #     return f"找到实体「{entity_name}」的信息，但未发现与问题相关的内容。"
        
        # # 3. 构建知识上下文（区分直接关联和间接关联）
        # kg_context = self._build_kg_context(filtered_kg_info)
        
        kg_context = kg_info
        # 4. 优化prompt模板，增加对信息优先级的提示
        answer_prompt = PromptTemplate(
            template="""请根据以下知识图谱信息回答问题。
        知识图谱信息（按相关性排序）:
        {kg_context}

        问题: {question}

        回答要求:
        1. 优先使用直接关联的信息，间接关联信息仅作为补充
        2. 只回答问题明确提到的内容，不添加无关信息
        3. 若信息存在冲突，以出现次数多的描述为准
        4. 用自然语言简洁回答，避免使用技术术语
        """,
            input_variables=["kg_context", "question"]
        )
        
        prompt = answer_prompt.format(kg_context=kg_context, question=question)
        return llm_generate(llm_model=llm_model, prompt=prompt)


    # 新增辅助方法：提取问题关键词
    def _extract_keywords(self, text: str) -> List[str]:
        """简单提取问题中的名词和动词作为关键词"""
        import jieba
        import jieba.posseg as pseg
        
        # 过滤词性：保留名词(n)、动词(v)、动名词(vn)
        allowed_pos = {'n', 'v', 'vn'}
        words = pseg.cut(text)
        return [word for word, pos in words if pos in allowed_pos]


    # 新增辅助方法：过滤知识图谱信息
    def _filter_kg_info(self, kg_info: List[Dict], keywords: List[str]) -> List[Dict]:
        """根据关键词过滤并排序知识图谱信息"""
        if not keywords:
            return kg_info
            
        # 为每条信息计算相关性分数
        scored_info = []
        for item in kg_info:
            score = 0
            # 检查关系描述中是否包含关键词
            if 'relationship_desc' in item and item['relationship_desc']:
                for kw in keywords:
                    if kw in item['relationship_desc']:
                        score += 2  # 关系描述匹配权重更高
            # 检查目标实体是否包含关键词
            if 'target_name' in item and item['target_name']:
                for kw in keywords:
                    if kw in item['target_name']:
                        score += 1
            scored_info.append((item, score))
        
        # 按分数降序排序，保留分数>0的信息
        return [item for item, score in sorted(scored_info, key=lambda x: x[1], reverse=True) if score > 0]


    # 新增辅助方法：构建知识上下文
    def _build_kg_context(self, kg_info: List[Dict]) -> str:
        """将知识图谱信息格式化为易读的上下文"""
        context_parts = []
        for i, item in enumerate(kg_info, 1):
            if 'mid_name' in item:  # 间接关联
                part = (f"{i}. 间接关联: {item['source_name']}({item['source_type']}) "
                        f"通过{item['relationship_type']}({item['relationship_desc']})与{item['mid_name']}({item['mid_type']})关联，"
                        f"再通过{item['second_relationship_type']}({item['second_relationship_desc']})与{item['target_name']}({item['target_type']})关联")
            else:  # 直接关联
                part = (f"{i}. 直接关联: {item['source_name']}({item['source_type']}) "
                        f"通过{item['relationship_type']}({item['relationship_desc']})与{item['target_name']}({item['target_type']})关联")
            context_parts.append(part)
        return "\n".join(context_parts)

# 使用示例
if __name__ == "__main__":

    # 1. 初始化知识图谱检索器
    kg_retriever = KnowledgeGraphRetriever()
    
    # 2. 定义问题和加载LLM模型
    query = "知识图谱是什么?不低于600字的回答"
    llm_model = build_model(mode="qwen3_32b")  # 假设已实现模型加载
    
    # 3. 从问题中提取实体和关系（聚焦“组织”和“工作内容”类型）
    entities, relationships = kg_retriever.query2entity_relation(
        llm_model=llm_model,
        input_text=query,
        entity_type="组织、人物、文件"
    )
    
    
    # 4. 基于核心实体查询知识图谱（过滤“负责”类关系，限制直接关联）
    kg_retriever_info = []
    for i,e in enumerate(entities):
        target_entity = e['entity_name']  # 核心实体：市城管委
        # 调用优化后的query_neo4j_by_entity：只查“负责”关系，深度为1（直接关联）
        e_info = kg_retriever.query_neo4j_by_entity(
            entity_name=target_entity,
            max_depth=1  # 只看直接关联的实体（避免间接信息干扰）
        )
    
        print('第{}个实体：{}，检索内容：{}'.format(i+1, target_entity, e_info))
        kg_retriever_info.append(e_info)
    # 5. 评估kg_retriever_info有用信息，理论应该有个大模型来实现，我暂时不写
    
    # kg_value_retriever = ''+ 
    # 6. 生成回答
    answer = kg_retriever.generate_answer(
        llm_model=llm_model,
        question=query,
        entity_name=target_entity,
        kg_info=kg_retriever_info
    )
    
    print("\n=== 生成的回答 ===")
    print(answer)
        