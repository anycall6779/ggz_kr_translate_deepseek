#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeepSeek API 안전 최적화 배치 번역기 (개선판)
- 괄호/특수문자 보호(「」『』【】 등)
- 플레이스홀더 보존/복원
- #BATCH_SPLIT 보정
- 429 및 content-filter 예외 처리 보강
- 불필요한 주석/노트 후처리 제거 강화
- batch_size 자동 감소 제거 (불일치 발생 시 개별 fallback 처리)
"""

import os
import json
import time
import random
import re
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential

# ---------------------------
# 파일 / 설정
# ---------------------------
TOKEN_PATH = r"C:\Users\hoho\Desktop\work\deepseek_token.txt"
INPUT_JSON_PATH = r"C:\Users\hoho\Desktop\work\original_texts_for_retranslation.json"
OUTPUT_JSON_PATH = r"C:\Users\hoho\Desktop\work\translated_output-final22525111111122223334444444555.json"
CHECKPOINT_PATH = OUTPUT_JSON_PATH.replace(".json", "_checkpoint.json")
GLOSSARY_PATH = r"C:\Users\hoho\Desktop\work\glossary-japan.json"

# ---------------------------
# DeepSeek (Azure) 초기화
# ---------------------------
with open(TOKEN_PATH, "r", encoding="utf-8") as f:
    lines = [line.strip() for line in f.readlines()]
DEEPSEEK_ENDPOINT = lines[0]
DEEPSEEK_API_KEY = lines[1]
API_VERSION = lines[2]
MODEL_NAME = lines[3]

client = ChatCompletionsClient(
    endpoint=DEEPSEEK_ENDPOINT,
    credential=AzureKeyCredential(DEEPSEEK_API_KEY),
    api_version=API_VERSION
)

# ---------------------------
# 용어집 로드
# ---------------------------
with open(GLOSSARY_PATH, "r", encoding="utf-8") as f:
    glossary = json.load(f).get("JP_TO_KR", {})

# ---------------------------
# 유틸 함수들
# ---------------------------
def clean_translation(result: str) -> str:
    """모델 응답에서 불필요한 태그/주석/설명 제거 (강화 버전)"""
    if not result:
        return ""

    text = result

    # <think>...</think> 블록 제거
    text = re.sub(r'<think>.*?</think>\n?', '', text, flags=re.DOTALL)

    # "**Translation Notes:**" 이후 전부 제거
    text = re.sub(r'\*\*Translation Notes:\*\*.*', '', text, flags=re.DOTALL)

    # "(Note: ...)" 같은 괄호 주석 제거
    text = re.sub(r'\(Note:.*?\)', '', text, flags=re.DOTALL)

    # 줄 단위에서 "Note:" 로 시작하는 문장 제거
    text = re.sub(r'^\s*Note:.*$', '', text, flags=re.MULTILINE)

    # "Translation Notes:" 단독 패턴도 제거
    text = re.sub(r'Translation Notes:.*', '', text, flags=re.DOTALL)

    return text.strip()

def fix_batch_markers(text: str) -> str:
    """모델이 #BATCH_SPLIT_x# 을 변형했을 때 보정"""
    text = text.replace('＃', '#')  # fullwidth # -> #
    text = re.sub(r'#BATCH[_\s]*SPIT_(\d+)#', r'#BATCH_SPLIT_\1#', text, flags=re.IGNORECASE)
    text = re.sub(r'#BATCH[_\s]*SPLlT_(\d+)#', r'#BATCH_SPLIT_\1#', text, flags=re.IGNORECASE)
    text = re.sub(r'#BATCH[_\s]*SPLIT[_\s]*(\d+)#', r'#BATCH_SPLIT_\1#', text, flags=re.IGNORECASE)
    return text


# ---------------------------
# 플레이스홀더 기반 전처리/후처리 (수정)
# ---------------------------
def preprocess_text(text: str):
    text = text or ""
    text = text.strip()

    placeholders = {}
    counter = 0

    token_re = re.compile(
        r'(#BATCH_SPLIT_\d+#|#n|#!ALB\([^)]*\)|<color=[^>]*?>|</color>|――|——|—|[「」｢｣『』【】〈〉《》“”‘’"“”])'
    )

    def _repl(m):
        nonlocal counter
        key = f"__PH_{counter}__"
        placeholders[key] = m.group(0)
        counter += 1
        return key

    protected = token_re.sub(_repl, text)

    # glossary 적용
    if glossary:
        for jp, kr in glossary.items():
            protected = protected.replace(jp, kr)

    return protected, placeholders


def postprocess_text(text: str, placeholders: dict):
    # PH_n는 존재하면 제거, 대신 원래 특수문자는 복원
    for k, v in placeholders.items():
        text = text.replace(k, v)
    # 만약 여전히 남은 PH_n 패턴이 있으면 제거
    text = re.sub(r'__PH_\d+__', '', text)
    return text.strip()




# ---------------------------
# 구조 복원 (#n 개수 맞추기 등)
# ---------------------------
def restore_structure(translated: str, source: str) -> str:
    source_n_count = source.count("#n")
    translated_n_count = translated.count("#n")
    if translated_n_count > source_n_count:
        translated = re.sub(r'#n', '', translated, count=(translated_n_count - source_n_count))
    elif translated_n_count < source_n_count:
        translated += "#n" * (source_n_count - translated_n_count)
    translated_sentences = [s.strip() for s in translated.split("#n") if s.strip()]
    final_sentences = []
    for s in translated_sentences:
        if s not in final_sentences:
            final_sentences.append(s)
    return "#n".join(final_sentences)

# ---------------------------
# 번역 요청 (단일 배치)
# ---------------------------
def translate_batch_text(batch_text: str) -> str:
    user_prompt = (
        f"{batch_text}\n\n"
        "Translate the content to Korean. Leave any English text unchanged. "
        "Do NOT change tokens that look like __PH_<number>__ or #BATCH_SPLIT_<number># or markers like #n, #!ALB(...), <color=...>. "
        "Preserve punctuation and bracket characters exactly as in the original placeholders. "
        "Output only the translated content; do not add explanations or notes."
    )

    system_msg = SystemMessage(content=(
        "You are a professional translator. Translate Japanese/Chinese to Korean. "
        "Keep English text unchanged. Do not modify placeholders or special markers. "
        "Return ONLY the translated text. Do not include explanations, notes, or comments."
    ))

    retries = 20
    wait_time = 2.0
    for attempt in range(retries):
        try:
            response = client.complete(
                messages=[system_msg, UserMessage(content=user_prompt)],
                max_tokens=4096,
                temperature=0.0,
                top_p=0.1,
                model=MODEL_NAME
            )
            result = response.choices[0].message.content
            result = clean_translation(result)
            result = fix_batch_markers(result)
            return result
        except Exception as e:
            s = str(e)
            if "429" in s or "Too Many Requests" in s:
                print(f"⚠️ 429 → {wait_time:.1f}s 대기 후 재시도 ({attempt+1}/{retries})")
                time.sleep(wait_time + random.uniform(0, 1))
                wait_time *= 2
                continue
            if "ResponsibleAIPolicyViolation" in s or "content_filter" in s:
                print("⚠️ content_filter 발생 → 프롬프트 간소화 후 재시도")
                try:
                    fallback_prompt = (
                        f"{batch_text}\n\n"
                        "Translate to Korean. Keep English unchanged. "
                        "Do not change placeholders or markers. "
                        "Output only translated text."
                    )
                    response2 = client.complete(
                        messages=[SystemMessage(content="Translate text to Korean. Keep placeholders unchanged."),
                                  UserMessage(content=fallback_prompt)],
                        max_tokens=4096,
                        temperature=0.0,
                        top_p=0.1,
                        model=MODEL_NAME
                    )
                    result = response2.choices[0].message.content
                    result = clean_translation(result)
                    result = fix_batch_markers(result)
                    return result
                except Exception as e2:
                    print(f"⚠️ fallback 실패: {e2}")
                    return batch_text
            print(f"⚠️ API 오류: {e}")
            return batch_text
    print("❌ 재시도 실패 → 원문 반환")
    return batch_text

# ---------------------------
# 배치 번역 (메인 루프)
# ---------------------------
def batch_translate(json_data, max_batch_size=10):
    keys = list(json_data.keys())
    translated_data = {}

    # 체크포인트 불러오기
    start_index = 0
    if os.path.exists(CHECKPOINT_PATH):
        with open(CHECKPOINT_PATH, "r", encoding="utf-8-sig") as f:
            checkpoint = json.load(f)
            translated_data = checkpoint.get("data", {})
            start_index = checkpoint.get("index", 0)
        print(f"🔄 체크포인트 불러오기: {start_index}/{len(keys)}")

    total = len(keys)
    i = start_index
    current_batch_size = max_batch_size

    while i < total:
        batch_keys = keys[i:i + current_batch_size]

        batch_text_list = []
        placeholders_list = []
        non_empty_keys = []

        for key in batch_keys:
            text = json_data.get(key, "")
            if not text or not str(text).strip():
                translated_data[key] = text
                continue
            pre_text, placeholders = preprocess_text(str(text))
            idx = len(batch_text_list)
            batch_text_list.append(f"#BATCH_SPLIT_{idx}#\n{pre_text}")
            placeholders_list.append(placeholders)
            non_empty_keys.append(key)

        if not batch_text_list:
            i += len(batch_keys)
            continue

        batch_input = "\n".join(batch_text_list)
        batch_output = translate_batch_text(batch_input)
        batch_output = fix_batch_markers(batch_output)

        split_output = re.split(r'#BATCH_SPLIT_\d+#\n', batch_output)
        split_output = [s.strip() for s in split_output if s.strip()]

        # 분할 개수 불일치 시 → 자동 batch_size 감소 대신 개별 번역 fallback
        # 분할 개수 불일치 시 → 임시로 batch_size 줄여서 재시도
        if len(split_output) != len(batch_text_list):
            print(f"⚠️ split_output({len(split_output)}) != batch({len(batch_text_list)}) → 임시 batch_size 축소 재시도")

            # 최소 단위로 나눠서 재번역 (예: batch_size 5)
            retry_size = max(3, min(5, len(batch_text_list)))  
            for k in range(0, len(batch_text_list), retry_size):
                sub_batch_keys = non_empty_keys[k:k+retry_size]
                sub_batch_texts = batch_text_list[k:k+retry_size]

                sub_input = "\n".join(sub_batch_texts)
                sub_output = translate_batch_text(sub_input)
                sub_output = fix_batch_markers(sub_output)

                sub_split = re.split(r'#BATCH_SPLIT_\d+#\n', sub_output)
                sub_split = [s.strip() for s in sub_split if s.strip()]

                if len(sub_split) != len(sub_batch_texts):
                    print(f"⚠️ 서브 배치 불일치 → 개별 번역 fallback 실행")
                    for j, key in enumerate(sub_batch_keys):
                        text = json_data[key]
                        pre_text, placeholders = preprocess_text(str(text))
                        translated = translate_batch_text(pre_text)
                        translated = fix_batch_markers(translated)
                        translated = postprocess_text(translated, placeholders)
                        translated = restore_structure(translated, text)
                        translated_data[key] = translated
                else:
                    for j, key in enumerate(sub_batch_keys):
                        translated_fragment = sub_split[j]
                        translated_fragment = postprocess_text(translated_fragment, placeholders_list[j])
                        translated_fragment = restore_structure(translated_fragment, json_data[key])
                        translated_data[key] = translated_fragment

            # 체크포인트 저장
            with open(OUTPUT_JSON_PATH, "w", encoding="utf-8") as f:
                json.dump(translated_data, f, ensure_ascii=False, indent=2)
            with open(CHECKPOINT_PATH, "w", encoding="utf-8") as f:
                json.dump({"index": i + len(batch_keys), "data": translated_data}, f, ensure_ascii=False, indent=2)

            i += len(batch_keys)
            time.sleep(random.uniform(3, 5))

            # ✅ 다음 루프에서는 다시 원래 batch_size로 복귀
            current_batch_size = max_batch_size
            continue

        # 정상 처리
        for j, key in enumerate(non_empty_keys):
            translated_fragment = split_output[j]
            translated_fragment = postprocess_text(translated_fragment, placeholders_list[j])
            translated_fragment = restore_structure(translated_fragment, json_data[key])
            translated_data[key] = translated_fragment

        with open(OUTPUT_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(translated_data, f, ensure_ascii=False, indent=2)
        with open(CHECKPOINT_PATH, "w", encoding="utf-8") as f:
            json.dump({"index": i + len(batch_keys), "data": translated_data}, f, ensure_ascii=False, indent=2)

        print(f"💾 {i + len(batch_keys)}/{total} 완료 및 저장")
        i += len(batch_keys)
        time.sleep(random.uniform(3, 5))

    if os.path.exists(CHECKPOINT_PATH):
        os.remove(CHECKPOINT_PATH)

    print(f"\n🎉 전체 번역 완료! 결과: {OUTPUT_JSON_PATH}")

# ---------------------------
# 실행
# ---------------------------
if __name__ == "__main__":
    with open(INPUT_JSON_PATH, "r", encoding="utf-8-sig") as f:
        input_json = json.load(f)
    batch_translate(input_json, max_batch_size=10)
