import json
import os
import re

def is_translation_broken_final(text):
    """
    번역된 텍스트의 오류 여부를 최종적으로 정밀하게 판단합니다.
    - 특수 기호(ーー, ・, α 등)는 허용합니다.
    - 실제 번역되지 않은 일본어(특히 히라가나)가 포함된 경우를 오류로 판단합니다.
    - AI의 주석 또는 플레이스홀더 설명이 포함된 경우를 오류로 판단합니다.
    """
    if not isinstance(text, str):
        return False

    # 1. AI의 생각 과정(영문) 또는 주석이 포함된 경우 -> 오류
    # --- 수정된 부분 ---
    # 사용자가 제공한 새로운 오류 유형(Note: ...)을 탐지하기 위해 패턴을 추가하고 구체화했습니다.
    broken_english_patterns = [
        # 기존 패턴
        "this is japanese", "translate to korean", "the segment is",
        "we must split it", "original:", "translation:", "combined:",
        "we must be cautious", "let's break down",
        # 새로 추가된 패턴
        "(note:",
        "actual translation",
        "placeholder \"xxx\"",
        "will be replaced with",
        "will be provided here",
        "remain intact",
        "translation",
        "Output",
        "<color=...>",
        "Translated",
        "japanese/chinese content"
    ]
    # ------------------

    text_lower = text.lower()
    for pattern in broken_english_patterns:
        if pattern in text_lower:
            return True

    # 2. 번역되지 않은 일본어 문자가 포함된 경우 -> 오류
    # 2-1. 히라가나(ぁ-ん)가 하나라도 포함되면 확실한 오류입니다.
    hiragana_pattern = re.compile(r'[\u3040-\u309F]')
    if hiragana_pattern.search(text):
        return True

    # 2-2. 가타카나(ァ-ン)의 경우, 이름 등에 쓰이는 중간점(・)을 제외하고
    #      다른 문자가 발견되면 오류로 판단합니다.
    katakana_pattern = re.compile(r'[\u30A0-\u30FA\u30FC-\u30FF]')
    if katakana_pattern.search(text):
        return True

    return False # 위의 조건에 해당하지 않으면 정상 번역으로 판단

def filter_json_file_final(input_path, good_output_path, broken_output_path):
    """
    최종 로직을 사용하여 JSON 파일을 정상/오류 번역으로 분리 저장합니다.
    """
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"오류: 파일을 찾을 수 없습니다. 경로를 확인해주세요: {input_path}")
        return
    except json.JSONDecodeError:
        print(f"오류: JSON 파일 형식이 올바르지 않습니다: {input_path}")
        return

    good_translations = {}
    broken_translations = {}

    for key, value in data.items():
        if is_translation_broken_final(value):
            broken_translations[key] = value
        else:
            good_translations[key] = value

    # 정상 번역 파일 저장
    with open(good_output_path, 'w', encoding='utf-8') as f:
        json.dump(good_translations, f, ensure_ascii=False, indent=4)

    # 오류 번역 파일 저장
    with open(broken_output_path, 'w', encoding='utf-8') as f:
        json.dump(broken_translations, f, ensure_ascii=False, indent=4)

    print("✨ 최종 필터링 작업이 완료되었습니다.")
    print(f"✅ 정상 번역 ({len(good_translations)}개) -> {os.path.basename(good_output_path)}")
    print(f"❌ 오류 번역 ({len(broken_translations)}개) -> {os.path.basename(broken_output_path)}")

if __name__ == '__main__':
    # --- 설정 ---
    # 필터링할 번역 파일 경로를 지정해주세요.
    # 예: "C:\\Users\\hoho\\Desktop\\work\\translated_output_end.json"
    INPUT_FILE_PATH = r"C:\Users\hoho\Desktop\new\translated_output_end3.json" # 이 경로를 실제 파일 위치로 변경하세요.

    # --- 실행 ---
    if os.path.exists(INPUT_FILE_PATH):
        base_dir = os.path.dirname(os.path.abspath(INPUT_FILE_PATH))
        # 결과 파일 이름 설정
        FINAL_CLEAN_PATH = os.path.join(base_dir, "final_clean_output.json")
        FINAL_BROKEN_PATH = os.path.join(base_dir, "final_broken_output.json")

        filter_json_file_final(INPUT_FILE_PATH, FINAL_CLEAN_PATH, FINAL_BROKEN_PATH)
    else:
        print(f"오류: 입력 파일 '{INPUT_FILE_PATH}'를 찾을 수 없습니다. 파일 경로를 확인해주세요.")