import json

# 두 파일의 전체 경로를 지정합니다.
# 'r'을 앞에 붙이면 경로에 있는 백슬래시(\)를 문자로 인식하여 편리합니다.
# 처음꺼는 넣어야할 항목입니다. 두번쨰가 결과물입니다.
source_file_path = r"C:\Users\hoho\Desktop\new\translated_output-final22525111111122223334444444555.json"
destination_file_path = r"C:\Users\hoho\Desktop\new\translated_output_end3.json"

try:
    # 덮어쓸 내용이 있는 파일(source)을 읽습니다.
    with open(source_file_path, 'r', encoding='utf-8') as f:
        source_data = json.load(f)

    # 기존 파일(destination)을 읽습니다.
    with open(destination_file_path, 'r', encoding='utf-8') as f:
        destination_data = json.load(f)

    # source_data의 내용으로 destination_data를 업데이트(덮어쓰기)합니다.
    # 같은 키(key)가 있다면 source_data의 값으로 변경됩니다.
    destination_data.update(source_data)

    # 업데이트된 내용을 다시 destination 파일에 씁니다.
    with open(destination_file_path, 'w', encoding='utf-8') as f:
        # ensure_ascii=False는 한글이 깨지지 않게 저장하기 위함입니다.
        # indent=4는 JSON 파일을 보기 좋게 4칸 들여쓰기하여 저장하는 옵션입니다.
        json.dump(destination_data, f, ensure_ascii=False, indent=4)

    print(f"🎉 성공! '{destination_file_path}' 파일에 내용을 성공적으로 덮어썼습니다.")

except FileNotFoundError:
    print("❌ 오류: 파일 경로를 찾을 수 없습니다. 경로가 올바른지 다시 확인해주세요.")
except json.JSONDecodeError:
    print("❌ 오류: JSON 파일 형식이 잘못되었습니다. 파일 내용이 올바른 JSON 구조인지 확인해주세요.")
except Exception as e:
    print(f"❌ 알 수 없는 오류가 발생했습니다: {e}")