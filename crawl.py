import requests
from bs4 import BeautifulSoup
import re
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

# 기본 URL 설정
base_url = "https://www.smpa.go.kr"
list_page_url = f"{base_url}/user/nd54882.do"

# User-Agent 설정(크롤링 차단 방지)
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"
}

# Selenium WebDriver 설정
options = Options()
options.add_argument("--headless")  # 브라우저 창 없이 실행
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
service = Service()
driver = webdriver.Chrome(service=service, options=options)

# 목록 페이지 요청
response = requests.get(list_page_url, headers=headers, timeout=10)
soup = BeautifulSoup(response.text, "lxml")

# 상세 페이지 URL 가져오기
detail_links = soup.select("table tr td:nth-of-type(2) a")
detail_page_urls = []

for link in detail_links:
    href = link["href"]
    match = re.search(r"goBoardView\('(/user/nd54882\.do)','View','(\d+)'\)", href)
    if match:
        actual_url = f"{base_url}{match.group(1)}?View&boardNo={match.group(2)}"
        detail_page_urls.append(actual_url)

print(f"상세 페이지 개수: {len(detail_page_urls)}")

# 상세 페이지 URL을 파일로 저장
output_text_dir = r"C:\\Users\\USER\\Downloads\\web_crwl\\download_url"
os.makedirs(output_text_dir, exist_ok=True)
print(f"URL 저장됨: {output_text_dir}")

text_file_path = os.path.join(output_text_dir, "detail_urls.txt")
with open(text_file_path, "w", encoding="utf-8") as text_file:
    for detail_url in detail_page_urls:
        text_file.write(detail_url + "\n")

print(f"상세 페이지 URL 저장 완료: {text_file_path}")

# 저장된 URL 파일을 읽어서 Selenium으로 PDF 다운
pdf_output_dir = r"C:\\Users\\USER\Desktop\\project_crwl\\web_crwl\\download_pdf"
os.makedirs(pdf_output_dir, exist_ok=True)

with open(text_file_path, "r", encoding="utf-8") as file:
    urls = file.readlines()

for idx, url in enumerate(urls):
    url = url.strip()
    if not url:
        continue
    
    print(f"PDF 다운로드 중: {url}")
    try:
        driver.get(url)
        time.sleep(3)  # 페이지 로딩 대기

        # PDF 파일만 다운
        try:
            pdf_buttons = driver.find_elements(By.XPATH, "//a[contains(@onclick, 'attachfileDownload') and contains(text(), '.pdf')]")
            for pdf_button in pdf_buttons:
                pdf_name = pdf_button.text.strip().replace("/", "_")  # 파일명에서 불가능한 문자 제거
                pdf_url = pdf_button.get_attribute("onclick")
                match = re.search(r"attachfileDownload\('(/common/attachfile/attachfileDownload.do)','(\d+)'\)", pdf_url)
                if match:
                    pdf_download_url = f"{base_url}{match.group(1)}?attachNo={match.group(2)}"
                    print(f"PDF 링크 발견: {pdf_download_url}")
                    pdf_response = requests.get(pdf_download_url, headers=headers, stream=True)
                    if pdf_response.status_code == 200:
                        pdf_path = os.path.join(pdf_output_dir, f"{pdf_name}")
                        with open(pdf_path, "wb") as pdf_file:
                            for chunk in pdf_response.iter_content(chunk_size=1024):
                                if chunk:
                                    pdf_file.write(chunk)
                        print(f"PDF 다운로드 완료: {pdf_path}")
                    else:
                        print(f"PDF 다운로드 실패: {pdf_download_url}")
        except Exception as e:
            print(f"PDF 다운로드 버튼을 찾을 수 없음: {url} ({e})")
    except Exception as e:
        print(f"PDF 다운로드 실패: {url} ({e})")

driver.quit()
print(f"모든 PDF가 {pdf_output_dir}에 저장됨.")


import os
import pandas as pd
import pdfplumber
import re

# 파일 경로 설정
pdf_input_dir = r"C:\\Users\\USER\Desktop\\project_crwl\\web_crwl\\download_pdf"
csv_output_dir = r"C:\\Users\\USER\Desktop\\project_crwl\\web_crwl\\output_txt_csv"
os.makedirs(csv_output_dir, exist_ok=True)

# 한자 변환 dict
char_replacements = {
    "出": "번 출구",
    "未定": "미정"
}

# 행정구역 패턴 (<> 안에 있는 텍스트 추출)
location_pattern = re.compile(r"<([^<>]+)>")

# PDF에서 표 추출 및 CSV 저장
for pdf_file in os.listdir(pdf_input_dir):
    if pdf_file.endswith(".pdf"):
        pdf_path = os.path.join(pdf_input_dir, pdf_file)
        csv_output_path = os.path.join(csv_output_dir, pdf_file.replace(".pdf", ".csv"))

        try:
            with pdfplumber.open(pdf_path) as pdf:
                all_tables = []

                for page in pdf.pages:
                    tables = page.extract_tables()
                    for table in tables:
                        df = pd.DataFrame(table)

                        # 컬럼 개수 확인 (5개 컬럼 유지)
                        if df.shape[1] < 5:
                            continue  
                        df = df.iloc[:, :5]  # 첫 5개 컬럼만 유지

                        # 컬럼명 정리
                        df.columns = ["집회 일시", "집회 장소(행진로)", "신고 인원", "관할서", "비고"]

                        # 행정구역(동) 분리
                        df["행정구역(동)"] = df["집회 장소(행진로)"].apply(lambda x: location_pattern.search(str(x)).group(1) if location_pattern.search(str(x)) else "")
                        df["집회 장소(행진로)"] = df["집회 장소(행진로)"].apply(lambda x: location_pattern.sub("", str(x)).strip())

                        # 한자 변환 처리
                        df = df.applymap(lambda x: ''.join([char_replacements.get(c, c) for c in str(x)]) if isinstance(x, str) else x)

                        all_tables.append(df)

                # 모든 페이지에서 표를 합쳐서 CSV 저장
                if all_tables:
                    final_df = pd.concat(all_tables, ignore_index=True)

                    # 0행 제거 (컬럼명이 중복될 가능성)
                    final_df = final_df.iloc[1:]

                    # CSV 저장
                    final_df.to_csv(csv_output_path, index=False, encoding="utf-8-sig")
                    print(f"CSV 저장 완료: {csv_output_path}")
                else:
                    print(f"표를 찾을 수 없음: {pdf_path}")

        except Exception as e:
            print(f"표 추출 실패: {pdf_path} ({e})")

print(f"모든 PDF에서 집회 일정이 {csv_output_dir}에 저장됨.")

import requests
import pandas as pd
import glob
import os

#CSV 파일이 저장된 폴더 경로
CSV_FOLDER = r"C:\Users\USER\Desktop\project_crwl\web_crwl\output_txt_csv"
API_URL = "http://127.0.0.1:8000/add_protest"  # FastAPI 서버 주소

def send_csv_to_api():
    csv_files = glob.glob(os.path.join(CSV_FOLDER, "*.csv"))  # 모든 CSV 파일 가져오기
    protests = []

    # CSV 파일 확인 및 데이터 읽기
    if not csv_files:
        print("CSV 파일이 없음음")
        return

    for file in csv_files:
        df = pd.read_csv(file)  # CSV 파일 읽기
        print(f"📄 {file}에서 데이터 읽음:")
        print(df.head())  # CSV 내용 확인

        # NaN 값 None으로 변환 (JSON 직렬화 오류 방지)
        df = df.where(pd.notna(df), None)

        #모든 데이터를 문자열로 변환 (JSON 변환 문제 방지)
        df = df.astype(str)

        # DataFrame을 JSON 리스트로 변환
        protests.extend(df.to_dict(orient="records"))

    # FastAPI로 데이터 전송
    if protests:
        print(f"📤 {len(protests)}개 데이터 전송 중")
        try:
            response = requests.post(API_URL, json={"protests": protests})
            print(f"응답 코드: {response.status_code}")
            print(f"응답 내용: {response.json()}")
        except requests.exceptions.RequestException as e:
            print(f"API 요청 실패: {e}")

if __name__ == "__main__":
    send_csv_to_api()  # CSV 데이터 FastAPI에 전송

