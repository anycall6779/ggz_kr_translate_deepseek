import json

# --- 설정 ---
# 정렬하고 싶은 원본 파일 이름을 여기에 입력하세요.
input_file_name = r"C:\Users\hoho\Desktop\new\translated_output_end.json"

# 정렬된 결과를 저장할 파일 이름을 여기에 입력하세요.
output_file_name = r"C:\Users\hoho\Desktop\new\translated_output_end2.json"
# --- 설정 끝 ---

try:
    # 1. JSON 파일 읽기
    with open(input_file_name, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"'{input_file_name}' 파일을 성공적으로 읽었습니다.")

    # 2. 키(key)를 정수(int)로 변환하여 숫자 순서대로 정렬
    # 각 키-값 쌍(item)에서 키(item[0])를 숫자로 바꿔 정렬 기준으로 사용합니다.
    sorted_data = dict(sorted(data.items(), key=lambda item: int(item[0])))
    print("데이터를 숫자 순서대로 정렬했습니다.")

    # 3. 정렬된 데이터를 새로운 JSON 파일로 저장
    with open(output_file_name, 'w', encoding='utf-8') as f:
        # ensure_ascii=False는 한글 등 다국어 문자가 깨지지 않도록 합니다.
        # indent=4는 JSON 파일을 보기 좋게 4칸 들여쓰기합니다.
        json.dump(sorted_data, f, ensure_ascii=False, indent=4)

    print(f"🎉 정렬 완료! '{output_file_name}' 파일에 결과를 저장했습니다.")
    print(f"총 {len(sorted_data)}개의 항목이 정렬되었습니다.")

except FileNotFoundError:
    print(f"❌ 오류: '{input_file_name}' 파일을 찾을 수 없습니다.")
    print("   스크립트 파일과 같은 폴더에 파일이 있는지, 파일 이름이 올바른지 확인해주세요.")
except (ValueError, TypeError):
    print("❌ 오류: 파일의 키(key) 중에 숫자로 바꿀 수 없는 값이 있습니다.")
except Exception as e:
    print(f"❌ 알 수 없는 오류가 발생했습니다: {e}")