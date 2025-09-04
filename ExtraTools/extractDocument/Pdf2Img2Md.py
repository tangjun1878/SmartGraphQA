import fitz  # PyMuPDF
import os
from PIL import Image
import base64
import io
import re
import sys
from langchain.schema import HumanMessage, SystemMessage

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# 假设这些模块存在并能导入
from Models.vision_models import build_mllm_model,infer_vl
from ExtraTools.extractDocument.extractPrompt import ExtractPrompt
from Models.LLM_Models import build_model, stream_invoke, remove_think



class PDFToMarkdownConverter:

    """
    这个类只处理一个pdf文件内容，并生成markdown文件
    """
    def __init__(self, pdf_path, # pdf文件路径，必须提供
                 output_folder, # 输出文件件，必须提供 
                 mllm_mode="qwen2.5vl_32b", # 决定使用哪个mllm模型
                 zoom=2,
                 save_md_interval=10, # pdf转成makedown格式每save_md_interval间隔保存一次，避免中途故障而没有保存任何内容
                 save_images=True,  # 是否保存pdf转成图片
                 prompt_pdf2md=None,  # 提供pdf图像转成md的prompt，否则调用模板内容
                 pdf_pages_start=None, # 指定pdf开始页码，如果为None表示不指定，从第一页开始。而格式为整数。
                 pdf_pages_end=None,  # 指定pdf结束页码，如果为None表示不指定，到最后一页结束。而格式为整数。
                 
                 prompt_revise_md=None, # 提供修正md的prompt，否则调用模板内容
                 use_revise=True, # 决定是否使用修正md的prompt
                 revise_md_interval = [5,10], # 修正md页面间隔，[5,10]表示参考前5页内容来校正后面的10页内容。当然参考后文也可以提供，但我没做。
                 revise_model_mode = None #如果为None，表示使用mllm多模态大模型，否则使用指定的语言模型，其格式为模型名称，如"qwen3_32b"
                 ):
        """



        """
        self.pdf_path = pdf_path
        self.output_folder = output_folder
        self.zoom = zoom
        self.base64_images = []  # 存储转换后的 Base64 图像字符串
        self.save_images = save_images  
        self.save_md_interval = save_md_interval
        self.prompt_pdf2md= ExtractPrompt["pdf2img2md"] if prompt_pdf2md is  None else prompt_pdf2md
        self.pdf_pages_start = pdf_pages_start
        self.pdf_pages_end = pdf_pages_end



        self.use_revise = use_revise
        
        if use_revise:
            self.prompt_revise_md = ExtractPrompt["revise_md"] if prompt_revise_md is None  else prompt_revise_md
        
        self.mllm_model = build_mllm_model(mode=mllm_mode)  # 多模态模型初始化
        self.revise_md_interval = revise_md_interval
        self.revise_llm_model = build_model(revise_model_mode) if revise_model_mode is not None else None

    def make_dir(self,out_dir):
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
        return out_dir


    def pdf_to_images(self):
        """
        将 PDF 每一页转为 Base64 图像流，并可选保存为 JPG 图像。
        """
        if self.output_folder is not None and self.save_images:
            out_dir = self.make_dir(os.path.join(self.output_folder, "pdf2img"))
            

        self.base64_images = [] # 清楚之前的内容
        doc = fitz.open(self.pdf_path)
        print(f"共 {len(doc)} 页")

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            mat = fitz.Matrix(self.zoom, self.zoom)
            pix = page.get_pixmap(matrix=mat)
            png_bytes = pix.tobytes()

            # 转换为 Base64 字符串
            base64_str = base64.b64encode(png_bytes).decode("utf-8")
            self.base64_images.append(base64_str)
            print(f"第 {page_num + 1} 页已转换为 Base64 字符串")

            # 保存为 JPG 图像（可选）
            if self.output_folder is not None and self.save_images:
                image = Image.open(io.BytesIO(png_bytes)).convert("RGB")
                img_path = os.path.join(out_dir, f"page_{page_num + 1}.jpg")
                image.save(img_path, "JPEG")
                print(f"图像保存至：{img_path}")

        doc.close()
        return self.base64_images

    # @staticmethod
    # def remove_markdown_markers(text: str, start_marker: str = "```markdown\n", end_marker: str = "\n```") -> str:
    #     """
    #     去除字符串首尾指定的 Markdown 代码块标记。
    #     """
    #     if text.startswith(start_marker):
    #         text = text[len(start_marker):]
    #     if text.endswith(end_marker):
    #         text = text[:-len(end_marker)]
    #     return text
    # import re

    def remove_markdown_markers(self,text):
        """
        去除字符串首尾的 Markdown 代码块标记，支持：
        - ```markdown ... ```
        - "```markdown ... ```"
        - '```py ... ```'
        并容忍引号、多余空格、换行等。
        """
        if not isinstance(text, str):
            return text

        # 去除开头：可选空格、引号、```、可选语言名、换行
        text = re.sub(r'^\s*["\']?```(?:[a-zA-Z]+)?\s*\n?', '', text)

        # 去除结尾：可选换行、```、可选引号、可选空白
        text = re.sub(r'\n?```["\']?\s*$', '', text)

        return text.strip()

    @staticmethod
    def extract_first_markdown_block(text):
        """
        提取第一个 Markdown 代码块中的内容。
        """
        pattern = r"```(?:markdown|md)?\s*\n(.*?)\s*```"
        match = re.search(pattern, text, re.DOTALL)
        return match.group(1).strip() if match else ""

    @staticmethod
    def save_markdown_content_to_file(content, filename="output.md"):
        """
        将 Markdown 内容保存为 .md 文件。
        """
        try:
            with open(filename, "w", encoding="utf-8") as file:
                file.write(content)
            print(f"✅ Markdown 内容已成功保存到文件：{filename}")
        except Exception as e:
            print(f"❌ 保存文件时出错：{e}")

    def generate_markdown(self, ):
        """
        通过视觉模型将图像流转为 Markdown 内容。

        :param prompt: dict，包含 system_prompt 和 user_prompt
        :param out_dir: 输出 Markdown 文件路径（可选）
        :param save_interval: 每隔多少张图保存一次（可选）
        :param max_pages: 最多处理多少页（可选）
        :return: 完整的 Markdown 内容
        """

        save_dir = self.make_dir(os.path.join(self.output_folder, "markdown"))
        save_generate_md = os.path.join(save_dir, "pdf2md_generate.md")
        save_revise_md = os.path.join(save_dir, "pdf2md_generate_revise.md")

        if not self.base64_images:
            raise ValueError("请先调用 pdf_to_images 生成图像流。")

        mllm_user_prompt = self.prompt_pdf2md.get('user_prompt',None)
        if not mllm_user_prompt:
            raise ValueError("user_prompt 是必需的")

        mllm_system_prompt = self.prompt_pdf2md.get('system_prompt',None)


        # 指定页码操作
        start_page=0 if self.pdf_pages_start is None else self.pdf_pages_start
        end_page=-1 if self.pdf_pages_end is None else self.pdf_pages_end
        images_to_process = self.base64_images[start_page:end_page]
        
        

        if self.use_revise:
            revise_user_prompt = self.prompt_revise_md.get('user_prompt',None)
            if not revise_user_prompt:
                raise ValueError("user_prompt 是必需的")
            revise_system_prompt = self.prompt_revise_md.get('system_prompt',None)
            revise_response_lst = []
            revise_response_makedown = ""


        response_markdown = ""
        for i, img in enumerate(images_to_process):
            print(f"正在处理第 {i + 1} 页pdf内容...")
            response = infer_vl(self.mllm_model,mllm_user_prompt, system_prompt=mllm_system_prompt, image=img)
            response = self.remove_markdown_markers(response)
            if self.use_revise:
                revise_response_lst.append(response)
                if len(revise_response_lst)>self.revise_md_interval[0]+self.revise_md_interval[1]:
                    revise_response_lst.pop(0)

            response = "\n" + response if response else response
            response_markdown += response

            if self.save_md_interval and (i + 1) % self.save_md_interval == 0:
                self.save_markdown_content_to_file(response_markdown, save_generate_md)
            
            if self.use_revise and (i + 1) % self.revise_md_interval[1] == 0:

                reference_content = "".join(revise_response_lst[:-self.revise_md_interval[1]])
                revise_content = "".join(revise_response_lst[-self.revise_md_interval[1]:])
                revise_prompt =revise_user_prompt.format(previous=reference_content,current=revise_content)

                revise_response = self.infer_revise_model(revise_system_prompt,revise_prompt)
                revise_response_makedown+=revise_response
                self.save_markdown_content_to_file(revise_response_makedown, save_revise_md)

                
        self.save_markdown_content_to_file(response_markdown, save_generate_md)
        if self.use_revise:
            self.save_markdown_content_to_file(revise_response_makedown, save_revise_md)

        return response_markdown

    def infer_revise_model(self,system_prompt, user_prompt):
        if self.revise_llm_model:
            message = []
            message.append(SystemMessage(content=system_prompt))
            message.append(HumanMessage(content=user_prompt))
            revise_response = stream_invoke(self.revise_llm_model, message)
        else:
            revise_response = infer_vl(self.mllm_model,user_prompt, system_prompt=system_prompt)
        revise_response = remove_think(revise_response)
        revise_response = self.remove_markdown_markers(revise_response)

        return revise_response



    def revise_markdown(self, markdown_content, prompt,model=None):
        """
        可选：对生成的 Markdown 内容进行格式校正。
        当前为预留接口，可扩展。
        """
        # 示例：调用模型对内容进行格式校正
        # response = infer_vl(prompt['user_prompt'], system_prompt=prompt.get('system_prompt'), image=None)
        # return self.extract_first_markdown_block(response)
        return markdown_content  # 占位返回


# 使用示例：
if __name__ == "__main__":
    pdf_file = '/extend_disk/d2/tj/langchain/SmartGraphQA-master/ExtraTools/extractDocument/example.pdf'
    output_folder = '/extend_disk/d2/tj/langchain/SmartGraphQA-master/ExtraTools/extractDocument/out_dir/example'


    converter = PDFToMarkdownConverter(pdf_file, 
                                       output_folder=output_folder, 
                                       zoom=2,
                                       mllm_mode="qwen2.5vl_32b", 
                                       save_md_interval=10, 
                                       save_images=True,  
                                       pdf_pages_start=None,
                                       pdf_pages_end=50,  
                                       use_revise=False, 
                                       revise_md_interval = [5,10], 
                                       revise_model_mode = None  # 示例 qwen3_14b                
                                       )
    converter.pdf_to_images()
    converter.generate_markdown()
