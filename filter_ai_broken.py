import json
import os

def extract_original_texts(original_file_path, broken_keys_file_path, output_file_path):
    """
    '오류 번역' 파일의 키 목록을 사용하여 '원본' 파일에서 해당 항목을 추출합니다.

    Args:
        original_file_path (str): 원본 텍스트가 포함된 JSON 파일 경로.
        broken_keys_file_path (str): 오류 번역 키가 포함된 JSON 파일 경로.
        output_file_path (str): 추출된 원본 텍스트를 저장할 파일 경로.
    """
    try:
        # 오류 번역 파일 로드하여 키 목록 가져오기
        with open(broken_keys_file_path, 'r', encoding='utf-8') as f:
            broken_data = json.load(f)
        broken_keys = set(broken_data.keys())
        print(f"'{os.path.basename(broken_keys_file_path)}'에서 {len(broken_keys)}개의 키를 찾았습니다.")

        # 원본 파일 로드
        with open(original_file_path, 'r', encoding='utf-8') as f:
            original_data = json.load(f)
        print(f"'{os.path.basename(original_file_path)}' 파일을 성공적으로 로드했습니다.")

    except FileNotFoundError as e:
        print(f"오류: 파일을 찾을 수 없습니다. 경로를 확인해주세요: {e.filename}")
        return
    except json.JSONDecodeError as e:
        print(f"오류: JSON 파일 형식이 올바르지 않습니다. 파일 내용을 확인해주세요. 오류: {e}")
        return

    # 오류 키에 해당하는 원본 데이터 추출
    extracted_data = {}
    for key in broken_keys:
        if key in original_data:
            extracted_data[key] = original_data[key]
        else:
            print(f"경고: 원본 파일에서 키 '{key}'를 찾을 수 없습니다.")

    # 추출된 데이터를 새 파일에 저장
    try:
        with open(output_file_path, 'w', encoding='utf-8') as f:
            json.dump(extracted_data, f, ensure_ascii=False, indent=4)
        print("\n추출 작업이 완료되었습니다.")
        print(f"✅ 총 {len(extracted_data)}개의 원본 텍스트를 추출하여 다음 파일에 저장했습니다:\n{output_file_path}")
    except IOError as e:
        print(f"오류: 파일을 저장하는 데 실패했습니다. {e}")


if __name__ == '__main__':
    # --- 설정 ---
    # 원본 파일 (일본어 텍스트) 경로
    ORIGINAL_FILE = r"C:\Users\hoho\Desktop\work\merged_output_12.0_sort1.json"
    
    # 이전에 필터링했던, 오류가 있는 번역 파일 경로
    BROKEN_TRANSLATION_FILE = r"C:\Users\hoho\Desktop\work\final_broken_output.json"

    # --- 실행 ---
    # 결과 파일이 저장될 경로 설정
    base_dir = os.path.dirname(os.path.abspath(ORIGINAL_FILE))
    OUTPUT_FILE = os.path.join(base_dir, "original_texts_for_retranslation.json")

    # 스크립트 실행
    extract_original_texts(ORIGINAL_FILE, BROKEN_TRANSLATION_FILE, OUTPUT_FILE)