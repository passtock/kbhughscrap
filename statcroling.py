import time
import re
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementClickInterceptedException, StaleElementReferenceException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# --- 1. 입력 데이터 파싱 (포지션 일반화 포함) ---
def parse_player_input(input_text):
    """사용자 입력을 파싱하여 선수 정보 리스트 생성"""
    players = []
    lines = input_text.strip().split('\n')
    for line in lines:
        line = line.strip()
        match = re.match(r'^\s*([^\s(]+)\s*\(([^,]+),\s*([^)]+)\)\s*$', line)
        if match:
            name = match.group(1).strip()
            school = match.group(2).strip()
            position = match.group(3).strip()
            # 포지션을 '타자' 또는 '투수'로 일반화
            if position in ['내야수', '외야수', '포수']:
                position = '타자'
            # 입력된 이름/학교가 li 태그 텍스트와 정확히 일치해야 함 (필요시 여기서 정제)
            players.append({'name': name, 'school': school, 'position': position})
        else:
            print(f"경고: 입력 형식 오류 - '{line}'")
    return players

# --- Helper Function: 드롭다운 옵션(<li>) 선택 (핵심 텍스트 비교) ---
def select_dropdown_option(driver, wait, dropdown_trigger_xpath, target_text, options_li_xpath, item_type="항목"):
    """
    드롭다운을 클릭하고, 표시된 <li> 옵션에서 핵심 텍스트가 일치하는 항목을
    찾아 스크롤 후 선택합니다. (괄호 안 내용 무시)
    **디버깅을 위해 모든 옵션 텍스트를 출력합니다.**
    """
    print(f"{item_type} 드롭다운 클릭 시도 (Trigger: {dropdown_trigger_xpath})...")
    try:
        trigger_element = driver.find_element(By.XPATH, dropdown_trigger_xpath)
        driver.execute_script("arguments[0].scrollIntoViewIfNeeded(true);", trigger_element)
        time.sleep(0.5)
        trigger = wait.until(EC.element_to_be_clickable((By.XPATH, dropdown_trigger_xpath)))
        driver.execute_script("arguments[0].click();", trigger)
        print(f"{item_type} 드롭다운 클릭 성공.")
        time.sleep(0.3)
    except TimeoutException:
        print(f"오류: {item_type} 드롭다운({dropdown_trigger_xpath})을 시간 내에 찾거나 클릭할 수 없습니다.")
        return False
    except Exception as e:
        print(f"{item_type} 드롭다운 클릭 중 오류: {e}")
        return False

    print(f"'{target_text}' {item_type} 검색 및 선택 시도 (Options XPath: {options_li_xpath})...")
    try:
        wait.until(EC.visibility_of_element_located((By.XPATH, options_li_xpath)))
        options = driver.find_elements(By.XPATH, options_li_xpath)
        print(f"  검색 대상 {item_type} 옵션 <li> {len(options)}개 발견. 전체 리스트:")
        print("-" * 30) # 구분선

        found = False
        clicked = False
        all_options_texts = [] # 모든 옵션 텍스트 저장용 리스트

        for i, option_li in enumerate(options): # 인덱스 추가
            try:
                option_full_text = option_li.text.strip()
                core_text = "" # 초기화
                if option_full_text:
                     # 핵심 텍스트 추출 (괄호 앞 부분)
                    core_text = option_full_text.split('(')[0].strip()

                # ★★★ 디버깅 출력: 모든 옵션의 전체 텍스트와 추출된 핵심 텍스트 출력 ★★★
                print(f"  [{i+1:02d}] Full: '{option_full_text}' || Core: '{core_text}'")
                all_options_texts.append(f"[{i+1:02d}] Full: '{option_full_text}' || Core: '{core_text}'") # 리스트에도 저장

                # 기본 옵션("팀명", "선수명" 등) 및 빈 텍스트 제외 후 비교
                if core_text and core_text != item_type+"명":
                    # 핵심 텍스트 비교
                    if core_text == target_text:
                        print(f"  >> 일치 항목 찾음: '{option_full_text}'. 스크롤 및 클릭 시도...")
                        found = True # 일단 찾았다고 표시
                        try:
                            driver.execute_script("arguments[0].scrollIntoViewIfNeeded(true);", option_li)
                            time.sleep(0.5)
                            driver.execute_script("arguments[0].click();", option_li)
                            print(f"  >> '{target_text}' {item_type} 선택 성공.")
                            clicked = True
                            time.sleep(0.5)
                            break # 성공했으므로 루프 탈출

                        except StaleElementReferenceException:
                            print(f"  >> 클릭 시도 중 StaleElementReferenceException 발생 ('{option_full_text}').")
                            return False # 클릭 실패 시 함수 실패
                        except Exception as click_err:
                            print(f"  >> 옵션 <li> 클릭 중 오류 발생 ('{option_full_text}'): {click_err}")
                            return False # 클릭 실패 시 함수 실패
            except StaleElementReferenceException:
                print(f"  [{i+1:02d}] 옵션 처리 중 StaleElementReferenceException 발생.")
                all_options_texts.append(f"[{i+1:02d}] StaleElementReferenceException 발생")
                continue
            except Exception as e:
                print(f"  [{i+1:02d}] 개별 옵션 <li> 처리 중 오류: {e}")
                all_options_texts.append(f"[{i+1:02d}] 처리 오류: {e}")
                continue

        print("-" * 30) # 구분선

        if not found:
            print(f"오류: '{target_text}' {item_type} 옵션을 리스트에서 찾을 수 없습니다.")
            print("=== 전체 옵션 리스트 (재확인) ===")
            for txt in all_options_texts: # 저장된 전체 리스트 다시 출력
                print(txt)
            print("===============================")
            # 실패 시 드롭다운 닫기 시도
            try:
                 body = driver.find_element(By.TAG_NAME, 'body')
                 body.click(); time.sleep(0.5)
            except: pass
            return False

        # 찾았지만 클릭 실패한 경우 (이론상 위에서 처리됨)
        if found and not clicked:
             print(f"오류: '{target_text}' {item_type}을 찾았으나 클릭에 실패했습니다.")
             return False

        return True # 최종 성공

    except TimeoutException:
         print(f"오류: {item_type} 옵션 리스트({options_li_xpath})가 시간 내에 나타나지 않았습니다.")
         return False
    except Exception as e:
        print(f"{item_type} 선택 중 오류: {e}")
        return False

# --- 2. Selenium을 이용한 스크래핑 함수 (전체 레코드 추출 및 URL 수정) ---
def scrape_player_stats(player_list, base_url):
    """Selenium을 사용하여 선수별 전체 기록 섹션 스크래핑 및 URL 조정"""

    all_player_data = {}

    print("WebDriver 설정 중...")
    try:
        service = Service(ChromeDriverManager().install())
        options = webdriver.ChromeOptions()
        # options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        driver = webdriver.Chrome(service=service, options=options)
        wait = WebDriverWait(driver, 15)
        print("WebDriver 설정 완료.")
    except Exception as e:
        print(f"WebDriver 설정 오류: {e}")
        return None

    # 드롭다운 트리거 XPath (이전과 동일하게 가정)
    school_dropdown_trigger_xpath = '//*[@id="recordForm"]/div/div[3]/div[1]/div[3]'
    player_dropdown_trigger_xpath = '//*[@id="recordForm"]/div/div[3]/div[1]/div[4]'
    position_dropdown_trigger_xpath = '//*[@id="recordForm"]/div/div[3]/div[1]/div[6]'

    # ★★★ 활성화된 드롭다운 내부의 <li> 옵션들을 찾는 XPath ★★★
    # 제공된 HTML 구조 기반: class 'abs_select'와 'on'을 모두 가진 div 내부의 ul 아래 li
    options_li_xpath = "//div[contains(@class, 'abs_select') and contains(@class, 'on')]//ul/li"

    # 전체 기록 Section을 찾는 XPath
    record_container_xpath = '//*[@id="Record"]/div[2]/div/div'

    for player in player_list:
        print(f"\n--- {player['name']} ({player['school']}, {player['position']}) 선수 전체 기록 스크래핑 시작 ---")
        record_html = "" # To store entire HTML content

        try:
            print(f"접속 시도: {base_url}")
            driver.get(base_url)
            # 페이지의 기본 요소(예: 학교 드롭다운)가 로드될 때까지 기다림
            wait.until(EC.presence_of_element_located((By.XPATH, school_dropdown_trigger_xpath)))
            time.sleep(1)

            # --- 상호작용: 수정된 Helper 함수와 XPath 사용 ---
            # 1. 학교 선택
            if not select_dropdown_option(driver, wait, school_dropdown_trigger_xpath, player['school'], options_li_xpath, "학교"):
                print(f"{player['name']} 선수 처리 중단 (학교 선택 실패).")
                continue

            # 2. 선수 선택 (핵심 이름 비교)
            if not select_dropdown_option(driver, wait, player_dropdown_trigger_xpath, player['name'], options_li_xpath, "선수"):
                print(f"{player['name']} 선수 처리 중단 (선수 선택 실패).")
                continue
            # 3. 포지션 검색 버튼 클릭
            print("검색 버튼 클릭 시도...")
            position_search_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="recordForm"]/div/div[3]/div[1]/div[6]/a')))
            driver.execute_script("arguments[0].scrollIntoViewIfNeeded(true);", position_search_button)
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", position_search_button)
            print("검색 버튼 클릭 성공.")
            time.sleep(1)


            # 4. 포지션에 따라 해당 항목 클릭
            try:
                if player['position'] == '타자':
                    position_xpath = '//*[@id="recordForm"]/div/div[3]/div[2]/ul/li[1]/a'
                elif player['position'] == '투수':
                    position_xpath = '//*[@id="recordForm"]/div/div[3]/div[2]/ul/li[2]/a'
                else:
                    print(f"알 수 없는 포지션: {player['position']}. 처리 중단.")
                    continue

                print(f"포지션 '{player['position']}' 항목 클릭 시도 (XPath: {position_xpath})...")
                position_element = wait.until(EC.element_to_be_clickable((By.XPATH, position_xpath)))
                driver.execute_script("arguments[0].scrollIntoViewIfNeeded(true);", position_element)
                time.sleep(0.5)
                driver.execute_script("arguments[0].click();", position_element)
                print(f"포지션 '{player['position']}' 항목 클릭 성공.")
                time.sleep(0.5)
            except TimeoutException:
                print(f"오류: 포지션 항목({position_xpath})을 시간 내에 클릭할 수 없습니다.")
                continue
            except Exception as e:
                print(f"포지션 항목 클릭 중 오류: {e}")
                continue
            print(driver.current_url) # 현재 URL 출력 (디버깅용)

            
            # 6. 전체 기록 섹션 내용 가져오기 (포지션에 따라 XPath 변경)
            if player['position'] == '타자':
                record_xpath = "//*[@id='Record']/div[2]"
            else:
                record_xpath = "//*[@id='Record']/div[1]"

            print(f"전체 기록 섹션 내용 추출 시도 (XPath: {record_xpath})...")
            try:
                record_container = wait.until(EC.presence_of_element_located((By.XPATH, record_xpath)))
                record_html = record_container.get_attribute('outerHTML')  # HTML 전체 가져오기
                print(f"  전체 기록 섹션 추출 성공 (길이: {len(record_html)} 문자).")
            except NoSuchElementException:
                print(f"오류: 기록 섹션 컨테이너({record_xpath})를 찾을 수 없습니다.")
            except TimeoutException:
                print(f"오류: 기록 섹션 컨테이너({record_xpath})가 시간 내에 로드되지 않았습니다.")
            except Exception as e:
                print(f"기록 섹션 추출 중 오류: {e}")

        except Exception as e:
            print(f"스크래핑 중 예기치 않은 오류 발생 ({player['name']}): {e}")
        finally:
            # HTML 문자열 저장
            if record_html:
                all_player_data[f"{player['name']}_{player['school']}"] = record_html
            else:
                all_player_data[f"{player['name']}_{player['school']}"] = "<h1>데이터 없음 또는 추출 실패</h1>"  # 오류시 HTML 저장
                print(f"{player['name']} 선수의 전체 기록을 찾지 못했거나 추출에 실패했습니다.")

        # HTML 내용을 보기 좋은 표 형태로 변환
        try:
            soup = BeautifulSoup(record_html, 'html.parser')
            profile_view = soup.find('div', class_='profile_view')
            if profile_view:
                rows = profile_view.find_all('li')
                headers = [header.text.strip() for header in rows[0].find_all('span')]
                data = [
                    [value.text.strip() for value in row.find_all('span')]
                    for row in rows[1:]
                ]
                df = pd.DataFrame(data, columns=headers)
                print(f"\n{player['name']} 선수의 기록 (표 형태):")
                print(df.to_string(index=False))  # 보기 좋게 출력
            else:
                print(f"{player['name']} 선수의 기록 섹션을 찾을 수 없습니다.")
        except Exception as e:
            print(f"{player['name']} 선수의 기록을 표 형태로 변환 중 오류 발생: {e}")

    print("\n모든 선수 스크래핑 완료. 브라우저 종료 중...")
    driver.quit()
    return all_player_data

# --- 3. Excel 파일로 저장 (수정됨 - 보기 좋은 데이터 저장) ---
def save_to_excel(data_dict, filename="kbo_player_stats_final.xlsx"):
    """스크래핑된 데이터를 Excel 파일로 저장 (표 형태 데이터)"""
    if not data_dict:
        print("저장할 데이터가 없습니다.")
        return

    try:
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            for sheet_name, html_content in data_dict.items():
                safe_sheet_name = re.sub(r'[\\/*?:\[\]]', '_', sheet_name)[:31]

                # HTML 내용을 DataFrame으로 변환
                try:
                    soup = BeautifulSoup(html_content, 'html.parser')
                    profile_view = soup.find('div', class_='profile_view')
                    if profile_view:
                        rows = profile_view.find_all('li')
                        headers = [header.text.strip() for header in rows[0].find_all('span')]
                        data = [
                            [value.text.strip() for value in row.find_all('span')]
                            for row in rows[1:]
                        ]
                        df = pd.DataFrame(data, columns=headers)
                        df.to_excel(writer, sheet_name=safe_sheet_name, index=False)
                        print(f"'{safe_sheet_name}' 시트에 데이터 저장 완료.")
                    else:
                        print(f"'{safe_sheet_name}' 시트에 저장할 데이터가 없습니다.")
                except Exception as e:
                    print(f"'{safe_sheet_name}' 시트 데이터 변환 중 오류 발생: {e}")

        print(f"\n데이터를 성공적으로 '{filename}' 파일에 저장했습니다.")
    except Exception as e:
        print(f"Excel 파일 저장 중 오류 발생: {e}")

# --- 실행 부분 (이전과 동일) ---
if __name__ == "__main__":
    input_player_data = """
    김진욱 (강릉고, 투수)
    김기중 (유신고, 투수)
    이재희 (대전고, 투수)
    나승엽 (덕수고, 내야수)
    김휘집 (신일고, 내야수)
    """ # 테스트 데이터 (이름, 학교, 포지션)

    #KBO 기본 URL (필터링 전)
    kbo_base_url = "https://www.korea-baseball.com/record/record/player_record?kind_cd=31&lig_idx=&group_no=&part_no=&record_type=1&begin_year=2020&end_year=2025&club_idx=&person_no=&group_part_idx="
    player_info_list = parse_player_input(input_player_data)

    if player_info_list:
        scraped_data = scrape_player_stats(player_info_list, kbo_base_url)
        if scraped_data:
            save_to_excel(scraped_data)
        else:
            print("스크래핑된 데이터가 없어 Excel 파일을 생성하지 않습니다.")
    else:
        print("처리할 선수 정보가 없습니다.")