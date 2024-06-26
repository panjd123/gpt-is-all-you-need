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


with open("key", "r") as f:
    API_KEY, BASE_URL = f.read().splitlines()

srcs_dir = r"D:\Download\8pDFS"

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

problem = """
用 C 或 C++ 实现 DFS 八数码问题，输出最优解的步数或者输出解的方案都可以。
请注意使用 DFS 是必须达到的要求，包括使用函数递归来实现 DFS 或者手写栈来实现 DFS 都可以。
但不能使用暴力 for 解决这个问题，否则视为没有完成该作业。
如果代码同时实现了 BFS 也可以。请提交材料说明自己的代码的正确性，比如评测平台的截图或者是例子。
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
如果没有完全按照要求提交材料，给70分，
如果没有按照要求实现，但是提供了代码，给60分，
如果没有代码，给50分，
如果交白卷，给0分。
如果提交了多份代码，按照最高分计算，比如有人交了暴力和DFS算法，我们要先根据 DFS 的代码打分，
不能因为另外提交的次优代码而降低分数，甚至应该表扬这种行为。
其次请附上简短的客观的评价，不需要说额外的废话，请注意提及是否按要求提交了题目要求的材料，比如正确性证明。
这是其中一位学生的作业：
%s
你的输出必须严格以 json 格式返回，例如
{{
    "score": 80,
    "comment": "作业完成度较高，按照要求提交了材料，但是存在一些小问题，例如变量命名不规范，需要改进"
}}
现在请给出你的评价输出，请注意，你的输出必须严格以 json 格式返回，否则会被视为无效输出。
"""

run_dir = "run" + osp.basename(srcs_dir)

if osp.exists(run_dir):
    os.system(f"rm -rf {run_dir}")

os.makedirs(run_dir)

if not osp.exists(srcs_dir):
    print("No srcs directory found")
    exit(1)

results = []


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
    if encoding is None:
        with open(file_path, "rb") as f:
            raw_data = f.read()
            encoding = chardet.detect(raw_data)["encoding"]

    choices = [
        encoding,
        "utf-8",
        "gb18030",
    ]

    for choice in choices:
        try:
            with open(file_path, mode, encoding=choice) as f:
                return f.read()
        except Exception as e:
            pass

    raise Exception("Failed to read file")


def smart_convert(file_path: str):
    if file_path.endswith(".docx") or file_path.endswith(".doc"):
        output = file_path.replace(".docx", ".md").replace(".doc", ".md")
        pypandoc.convert_file(file_path, "md", outputfile=output)
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


def deal_with(student_id, student_name, folder):
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
                ):
                    file_contents.append(
                        f"这是一张图片，文件名为：{file}，可能是学生提交的截图"
                    )
                elif (
                    file.endswith(".exe")
                    or file.endswith(".dll")
                    or file.endswith(".so")
                    or file.endswith(".a")
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
        json_str = response.splitlines()[1:-1]
        json_str = "\n".join(json_str)
        try:
            data = json.loads(json_str)
            score = data["score"]
            comment = data["comment"]
            return score, comment
        except Exception as e:
            print(json_str)
            return None, json_str

    score, comment = grade(contents)
    # results.append([student_id, student_name, score, comment])
    return score, comment


if __name__ == "__main__":
    try:
        for root, dirs, files in os.walk(srcs_dir):
            for file in tqdm.tqdm(files):
                student_id, student_name, file_name = file.split("_", 2)
                folder = None
                if file.endswith(".zip"):
                    with zipfile.ZipFile(osp.join(root, file), "r") as z:
                        for zfile in z.namelist():
                            try:
                                filename = zfile.encode("cp437").decode("gbk")
                            except:
                                filename = zfile
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
                    score, comment = deal_with(student_id, student_name, folder)
                elif (
                    file.endswith(".rar")
                    or file.endswith(".7z")
                    or file.endswith(".tar")
                    or file.endswith(".tar.gz")
                ):
                    score, comment = 0, f"Unsupport file type: {file}"
                else:
                    os.makedirs(osp.join(run_dir, student_id), exist_ok=True)
                    os.system(
                        f"cp {osp.join(root, file)} {osp.join(run_dir, student_id)}"
                    )
                    folder = osp.join(run_dir, student_id)
                    score, comment = deal_with(student_id, student_name, folder)

                tqdm.tqdm.write(f"{student_id} {student_name} {score} {comment}")

                results.append([student_id, student_name, score, comment])
    except KeyboardInterrupt:
        pass

    df = pd.DataFrame(results, columns=["学号", "姓名", "成绩", "评语"])
    df.to_excel("result.xlsx", index=False)
    df.to_csv("result.csv", index=False)
