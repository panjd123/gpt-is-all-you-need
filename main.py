import os
import os.path as osp
import tqdm
import pandas as pd
import zipfile
from openai import OpenAI
import json
import chardet
import pypandoc
import fitz
import argparse

parser = argparse.ArgumentParser()

parser.add_argument("--key-file", type=str, default="key", help="API key file")

parser.add_argument(
    "--dir",
    type=str,
    default=r"D:\Download\tic-tac-toe",
    help="Directory of student's homework",
)

args = parser.parse_args()

if args.key_file and osp.exists(args.key_file):
    with open(args.key_file, "r") as f:
        API_KEY, BASE_URL = f.read().splitlines()
else:
    raise FileNotFoundError(
        f"API key file {osp.abspath(args.key_file)} not found, please check the path"
    )

homework_dir = args.dir

if not osp.exists(homework_dir):
    raise FileNotFoundError(f"Directory {homework_dir} not found")

# problem = """
# 用 C 或 C++ 实现 DFS 八皇后问题，输出解的个数或者输出解的方案都可以。
# 请注意使用 DFS 是必须达到的要求，包括使用函数递归来实现 DFS 或者手写栈来实现 DFS 都可以。
# 但不能使用暴力for解决这个问题，否则视为没有完成该作业。
# """

# problem = """
# 用 C 或 C++ 实现 BFS 八数码问题，输出最优解的步数或者输出解的方案都可以。
# 请注意使用 BFS 是必须达到的要求，但不能使用暴力算法解决这个问题，否则视为没有完成该作业。
# 如果代码同时实现了 DFS 也可以。请提交材料说明自己的代码的正确性，比如评测平台的截图或者是例子。
# """

# problem = """
# 用 C 或 C++ 实现 DFS 八数码问题，输出最优解的步数或者输出解的方案都可以。
# 请注意使用 DFS 是必须达到的要求，包括使用函数递归来实现 DFS 或者手写栈来实现 DFS 都可以。
# 但不能使用暴力 for 解决这个问题，否则视为没有完成该作业。
# 如果代码同时实现了 BFS 也可以。请提交材料说明自己的代码的正确性，比如评测平台的截图或者是例子。
# """

problem = """
补充 Max_Value 和 Min_Value 两个函数实现 Min-Max 搜索的 tic-tac-toe AI。
你需要提交的材料包括：
代码和报告，报告内容包括运行结果和对于 Min-Max 算法的理解。
运行结果可以是图片，也可以是文本。
"""

prompt = f"""以下是学生的作业内容，我们的题目是：
{problem}
现在请你给出一个50到100之间的分数，
我们的评分标准要考察代码的可读性是否良好，是否有注释，性能是否优异，我们的学生是代码初学者，
不要过于苛刻：
只要基本完成任务要求就可以 80 分以上，
完成良好的 90 分，
特别优秀的给 100 分，
其中 80 分以下的例子如下：
如果疑似是借助网络，AI （比如 GPT）等工具生成的代码（即使中间替换了变量名，函数名等试图掩盖）的，且报告或者注释中没有体现处自己的思考，给 50 分，
如果没有完全按照要求提交材料，给70分，
如果没有按照要求实现，但是提供了代码，给60分，
如果没有代码，给50分，
如果交白卷，给0分。
如果提交了多份代码，按照最高分计算，比如有人交了暴力和DFS算法，我们要先根据 DFS 的代码打分，
不能因为另外提交的次优代码而降低分数，甚至应该表扬这种行为。
其次请附上简短的客观的评价，不需要说额外的废话，请注意提及是否按要求提交了题目要求的材料，比如正确性证明。
这是其中一位学生的作业，在读的过程中，如果你遇到 ![](media/image1.png){{width=1.663888888888889in height=9.686805555555555in}} 这样的图片，
请注意这是学生提交的截图，这大概率是运行结果。
以及部分时候，我会通知你，这是一张图片，文件名为：xxx，大概率是学生提交的运行结果截图。
%s
你的输出必须严格以 json 格式返回，例如
{{
    "score": 70,
    "comment": "作业完成度较高，有一定的注释，函数逻辑合理。但变量命名有点随意，而且没有提交图片或者上传文本证明自己的正确性，怀疑实现有误。"
}}
现在请给出你的评价输出，请注意，你的输出必须严格以 json 格式返回，否则会被视为无效输出。
"""


def get_gpt_response(prompt: str, model: str):
    client = OpenAI(
        api_key=API_KEY,
        base_url=BASE_URL,
    )

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model=model,
    )
    return chat_completion


def smart_read(file_path, mode="r", encoding=None):
    """
    尝试多种编码读取文件，返回读取的内容。

    如果多种编码都无法读取，则返回用自动检测的编码忽略错误后读取的内容。
    """

    if encoding is None:
        with open(file_path, "rb") as f:
            raw_data = f.read()
            encoding = chardet.detect(raw_data)["encoding"]

    choices = [
        encoding,
        "utf-8",
        "gb2312",
        "gb18030",
    ]

    for choice in choices:
        try:
            with open(file_path, mode, encoding=choice) as f:
                return f.read()
        except Exception as e:
            pass

    with open(file_path, mode, encoding=encoding, errors="ignore") as f:
        return f.read()


def smart_convert(file_path: str):
    """
    将 docx, pdf 文件转换为同名 md 文件，删除原文件，返回新文件路径。

    如果无法解析文件，会抛出异常。
    """

    if " " in file_path:
        assert False, "File path contains space"

    if file_path.endswith(".docx") or file_path.endswith(".doc"):
        output = file_path.replace(".docx", ".md").replace(".doc", ".md")
        try:
            pypandoc.convert_file(file_path, "md", outputfile=output)
        except Exception as e:
            print("Failed to convert file: ", file_path)
            raise e
        os.remove(file_path)
        return output
    if file_path.endswith(".pdf"):
        output = file_path.replace(".pdf", ".md")
        with fitz.open(file_path) as doc:
            text = ""
            for page in doc:
                text += page.get_text()
        with open(output, "w", encoding="utf-8") as f:
            f.write(text)
        os.remove(file_path)
        return output

    else:
        return file_path


def deal_with(folder):
    if folder is None:
        return 0, "Unsupport file type"

    file_contents = []

    try:
        for root, dirs, files in os.walk(folder):
            for file in files:
                if (
                    file.endswith(".png")
                    or file.endswith(".jpg")
                    or file.endswith(".jpeg")
                    or file.endswith(".gif")
                    or file.endswith(".bmp")
                ):
                    file_contents.append(
                        f"这是一张图片，文件名为：{file}，大概率是学生提交的运行结果截图。"
                    )
                elif (
                    file.endswith(".exe")
                    or file.endswith(".dll")
                    or file.endswith(".so")
                    or file.endswith(".a")
                    or file.endswith(".o")
                    or file.startswith(".")
                    or file.startswith("~")
                ):
                    continue
                else:
                    file_path = osp.join(root, file)
                    file_path = smart_convert(file_path)
                    file_contents.append(smart_read(file_path))
    except Exception as e:
        return 0, str(e)

    contents = "\n".join(file_contents)

    def grade(assignment_text, model="gpt-4o-2024-05-13"):
        response = get_gpt_response(prompt % assignment_text, model=model)
        return extract_score_and_comment(response.choices[0].message.content.strip())

    def extract_score_and_comment(response: str):
        """
        ```json
        {
            "score": 70,
            "comment": "作业完成度较高，但没有提交图片或者上传文本证明自己的正确性，我们有理由怀疑是错误的实现。"
        }
        ```
        """
        if response.startswith("```"):
            json_str = response.splitlines()[1:-1]
        else:
            json_str = response.splitlines()
        json_str = "\n".join(json_str)
        try:
            data = json.loads(json_str)
            score = data["score"]
            comment = data["comment"]
            return score, comment
        except Exception as e:
            with open("error.txt", "w") as f:  # 保存没法解析的 json 字符串
                f.write(json_str)
            return None, json_str

    score, comment = grade(contents)
    return score, comment


def main():
    run_dir = "run" + osp.basename(homework_dir)

    if osp.exists(run_dir):
        os.system(f"rm -rf {run_dir}")

    os.makedirs(run_dir)

    results = []
    try:
        for root, dirs, files in os.walk(homework_dir):
            for file in tqdm.tqdm(files):
                # 解压或拷贝一个学生的作业到对应的文件夹中，调用 deal_with 函数处理
                try:
                    student_id, student_name, file_name = file.split("_", 2)
                except ValueError:
                    print(f"Invalid file name: {file}")
                    continue
                folder = None
                if file.endswith(".zip"):  # 解压
                    with zipfile.ZipFile(osp.join(root, file), "r") as z:
                        for zfile in z.namelist():
                            try:
                                filename = zfile.encode("cp437").decode("gbk")
                            except:
                                filename = zfile
                            filename = filename.replace(" ", "_")
                            z.extract(zfile, osp.join(run_dir, student_id))
                            dirname = osp.join(
                                run_dir, student_id, osp.dirname(filename)
                            )
                            if not osp.exists(dirname) and dirname != "":
                                os.makedirs(dirname)
                            if filename != zfile:
                                os.system(
                                    f"mv '{osp.join(run_dir, student_id, zfile)}' '{osp.join(run_dir, student_id, filename)}'"
                                )
                    folder = osp.join(run_dir, student_id)
                    score, comment = deal_with(folder)
                elif (  # 什么鬼格式
                    file.endswith(".rar")
                    or file.endswith(".7z")
                    or file.endswith(".tar")
                    or file.endswith(".tar.gz")
                ):
                    score, comment = 0, f"Unsupport file type: {file}"
                else:  # 拷贝
                    os.makedirs(osp.join(run_dir, student_id), exist_ok=True)
                    os.system(
                        f"cp {osp.join(root, file)} {osp.join(run_dir, student_id)}"
                    )
                    folder = osp.join(run_dir, student_id)
                    score, comment = deal_with(folder)

                tqdm.tqdm.write(f"{student_id} {student_name} {score} {comment}")

                results.append([student_id, student_name, score, comment])
    except KeyboardInterrupt:
        pass

    df = pd.DataFrame(results, columns=["学号", "姓名", "成绩", "评语"])
    df.to_excel("result.xlsx", index=False)
    df.to_csv("result.csv", index=False)


main()
