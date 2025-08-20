from langchain_core.embeddings import Embeddings
import openai



# 给出默认参数字典的导入内容

embed_config = {
    "bge-m3": {
        "model": "bge-m3:latest",
        "api_url": "http://182.140.215.20:6542/v1",
        "api_key_embeddings": "sk-RJaJE4fXaktHAI2MB295F6Ad58004f7eBcE255B863CdD6F0"
    },
    "bge-large-zh-v1.5": {
        "model": "quentinz/bge-large-zh-v1.5:latest",
        "api_url": "http://182.140.215.20:6542/v1",
        "api_key_embeddings": "sk-RJaJE4fXaktHAI2MB295F6Ad58004f7eBcE255B863CdD6F0"
    },
    "bge-reranker-v2-m3": {
        "model": "q1lama/bge-reranker-v2-m3:latest",
        "api_url": "http://182.140.215.20:6542/v1",
        "api_key_embeddings": "sk-RJaJE4fXaktHAI2MB295F6Ad58004f7eBcE255B863CdD6F0"
    },
    "bge-large": {
        "model": "bge-large:latest",
        "api_url": "http://182.140.215.20:6542/v1",
        "api_key_embeddings": "sk-RJaJE4fXaktHAI2MB295F6Ad58004f7eBcE255B863CdD6F0"
    },
    
}

class EmbeddingsModels(Embeddings):
    def __init__(self, **kwargs):
        
        self.embed_model_name = embed_config["bge-m3"]["model"]
        self.config = embed_config["bge-m3"]
        self.kwargs = kwargs

        self.embed_model = self.build_embeddings_models()
  
       
   


    # 使用openai的接口来构建embedding模型
    def create_embed_model_openai(self):
        client_params = {
            "api_key": self.config.get("api_key_embeddings"),
            "base_url": self.config.get("api_url"),
            "timeout": self.config.get("timeout",None),
            "max_retries": self.config.get("max_retries", 2),
            "default_headers": self.config.get("default_headers", None),
            "default_query": self.config.get("default_query",None),
        }
        # 初始化同步客户端
        client = openai.OpenAI(**client_params).embeddings
         # # 初始化异步客户端
        # self.async_client = openai.AsyncOpenAI(**client_params).embeddings
        return client


    @property
    def _invocation_params(self):
        # 返回调用参数字典，包含模型名称
        params = {"model": self.embed_model_name}
        return params



    # openai接口实现的嵌入方法
    def _get_len_safe_embeddings_openai(self, texts,**kwargs):
        # 初始化批量嵌入列表
        batched_embeddings = []
        # 遍历文本列表
        for text in texts:
            # 调用OpenAI API生成嵌入
            response = self.embed_model.create(input=text, model=self.embed_model_name)
            # 如果响应不是字典类型，则转换为字典
            if not isinstance(response, dict):
                response = response.model_dump()
            # 将响应中的嵌入扩展到批量嵌入列表中
            batched_embeddings.extend(r["embedding"] for r in response["data"])
        return batched_embeddings



        
    # 这个函数根据不同的embed_mode来构建不同的embedding模型
    def build_embeddings_models(self):
        # 不存在embed_mode参数，则报错提醒

        embed_model = self.create_embed_model_openai()
      
        return embed_model

    # 下面是根据不同接口来调用不同的方法，这里只实现了openai的接口，后面可以添加其他的接口
    def embed_documents(self, texts,  **kwargs):

        return self._get_len_safe_embeddings_openai(texts, **kwargs)
       
    def embed_query(self, text):
        # 将单个文本转换为列表并调用embed_documents方法，然后返回第一个嵌入
        return self.embed_documents([text])[0]



def embed_demo():
    # nomic-embed-text:latest  274  bge-large:latest 670多   bge-m3:latest
   
    model = EmbeddingsModels()
    # data = ["今天天气很好", "我们很开心，和大家一起出来玩"]
    # embedding = model.embed_query(data[0])  # 注意这里应该是单个字符串而不是列表
    # embedding = model.embed_documents(data)  # 注意这里应该是列表
    # print(embedding)
    return model

if __name__ == "__main__":
    model = EmbeddingsModels()
    print(model.embed_query(["今天天气很好"]))

