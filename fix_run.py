import dirtyjson
import json

# ------------------- 설정 ------------------- #
# 여기에 문제가 있는 원본 JSON 파일 이름을 입력하세요.
INPUT_FILENAME = r"C:\Users\hoho\Desktop\new\translated_output_end2.json"

# 복구 후 새로 저장될 파일의 이름입니다.
OUTPUT_FILENAME = r"C:\Users\hoho\Desktop\new\translated_output_end3.json"
# ------------------------------------------- #


def repair_json_file(input_path, output_path):
    """
    dirtyjson 라이브러리를 사용하여 손상된 JSON 파일을 복구합니다.
    """
    print(f"'{input_path}' 파일의 복구를 시작합니다...")

    try:
        # 1. 손상된 파일을 텍스트 모드로 읽습니다.
        with open(input_path, 'r', encoding='utf-8') as f:
            broken_content = f.read()

        # 2. dirtyjson을 사용해 파이썬 객체로 로드합니다.
        # 이 과정에서 대부분의 문법 오류가 자동으로 수정됩니다.
        print(" -> 문법 오류를 분석하고 수정하는 중...")
        python_object = dirtyjson.loads(broken_content)

        # 3. 수정된 객체를 표준 JSON 형식으로 다시 파일에 씁니다.
        # indent=2 옵션으로 가독성을 높이고,
        # ensure_ascii=False 옵션으로 한글이 깨지지 않게 합니다.
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(python_object, f, indent=2, ensure_ascii=False)

        print(f"✅ 복구 성공! '{output_path}' 파일로 저장되었습니다.")

    except Exception as e:
        print(f"❌ 복구 실패: 파일을 처리하는 중 오류가 발생했습니다.")
        print(f"오류 내용: {e}")


# 스크립트 실행
if __name__ == "__main__":
    repair_json_file(INPUT_FILENAME, OUTPUT_FILENAME)