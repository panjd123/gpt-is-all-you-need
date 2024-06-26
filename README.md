# gpt-is-all-you-need

## How to use

```
choco install pandoc # 手动安装 pandoc
pip install pypandoc PyMuPDF openai tqdm pandas chardet
python main.py # 自动打分并生成评语，你需要修改文件开头的 API_KEY, BASE_URL, problem, prompt 变量以满足你的需求
python manual.py # 手动校准，会过一遍 THRESHOLD(文件开头) 以下分数的结果，你可以此时手动打分和评语
python output.py # 做一遍分数映射，同时删除评价列
```

## 说明

目前的功能包括：

- 解压 .zip 压缩包（只能解压一层）
- 解析 PDF, DOCX 到 Markdown
- 将文本类文件合并到 prompt 中向 GPT 提问
- 图片会告知 GPT 这里有一个图片，但是不能直接输入图片（API 限制）