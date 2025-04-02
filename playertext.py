import re

def format_player_data(input_text):
    """
    주어진 텍스트 데이터를 파싱하여 '이름 (최종출신학교, 포지션)' 형식으로 변환합니다.

    Args:
        input_text (str): 여러 줄로 구성된 선수 정보 문자열.
                          각 줄은 '이름 (학교1-학교2... 포지션)' 형식을 따르거나,
                          라운드 구분자 ('숫자 →') 형태입니다.

    Returns:
        list: '이름 (최종출신학교, 포지션)' 형식의 문자열 리스트.
    """
    lines = input_text.strip().split('\n')
    formatted_players = []

    for line in lines:
        line = line.strip()

        # 빈 줄이나 라운드 구분자(예: '2 →')는 건너<0xEB><0x9C><0x8C>니다.
        if not line or re.match(r'^\d+\s*→$', line):
            continue

        # 정규 표현식을 사용하여 이름, 학교(들), 포지션을 추출합니다.
        # 그룹 1: 이름 (공백 앞까지)
        # 그룹 2: 괄호 안의 내용 (학교 및 포지션)
        match = re.match(r'^\s*([^\s(]+)\s*\((.+)\)\s*$', line)

        if match:
            name = match.group(1).strip()
            details = match.group(2).strip()

            # 괄호 안 내용을 공백 기준으로 분리 (마지막이 포지션)
            detail_parts = details.split()

            if len(detail_parts) >= 2:
                position = detail_parts[-1]
                school_part = " ".join(detail_parts[:-1]) # 학교 부분을 다시 합침

                # 최종 출신 학교 추출 (하이픈(-)이 있으면 마지막 부분, 없으면 전체)
                if '-' in school_part:
                    final_school = school_part.split('-')[-1].strip()
                else:
                    final_school = school_part.strip()

                formatted_players.append(f"{name} ({final_school}, {position})")
            else:
                print(f"경고: '{line}' 라인에서 학교/포지션 정보를 제대로 분리할 수 없습니다.")

        # 정규 표현식에 맞지 않는 다른 형식의 입력 처리 (예: 괄호가 없는 경우 등)
        # 여기서는 주어진 형식을 기준으로 하므로, 맞지 않으면 건너뛰거나 경고를 출력합니다.
        else:
             # 이름, 학교, 포지션이 공백으로만 구분된 경우 시도
             parts = line.split()
             if len(parts) >= 3:
                 name = parts[0]
                 position = parts[-1]
                 school_part = " ".join(parts[1:-1])

                 if '-' in school_part:
                     final_school = school_part.split('-')[-1].strip()
                 else:
                     final_school = school_part.strip()
                 formatted_players.append(f"{name} ({final_school}, {position})")
             else:
                print(f"경고: '{line}' 라인은 예상된 형식이 아닙니다.")


    return formatted_players

# 입력 데이터 (사용자가 제공한 스타일을 한 줄 형식으로 재구성)
# 실제 입력 시에는 각 선수 정보가 한 줄에 있어야 합니다.
input_data = """
김진욱 (강릉고 투수)
김기중 (유신고 투수)
이재희 (대전고 투수)
박건우 (덕수고-고려대 투수)
권동진 (세광고-원광대 내야수)
김주원 (유신고 내야수)
이영빈 (세광고 내야수)
조형우 (광주제일고 포수)
김휘집 (신일고 내야수)
김동주 (선린인터넷고 투수)
2 →
나승엽 (덕수고 내야수)
송호정 (서울고 내야수)
홍무원 (경기고 투수)
장민기 (마산용마고 투수)
한차현 (포철고-성균관대 투수)
이용준 (서울디자인고 투수)
김진수 (군산상고-중앙대 투수)
고명준 (세광고 내야수)
김준형 (성남고 투수)
최승용 (소래고 투수)
3 →
김창훈 (경남고 투수)
조은 (대전고 투수)
오현석 (안산공고 내야수)
이승재 (휘문고-강릉영동대 투수)
유준규 (군산상고 내야수)
오장한 (장안고 외야수)
조건희 (서울고 투수)
조병현 (세광고 투수)
김성진 (부산정보고-계명대 투수)
강현구 (인천고 외야수)
4 →
송재영 (라온고 투수)
장규현 (인천고 포수)
주한울 (배명고 외야수)
권혁경 (신일고 포수)
지명성 (신일고 투수)
한재승 (인천고 투수)
이믿음 (강릉고-강릉영동대 투수)
장지훈 (김해고-동의대 투수)
이주형 (야탑고 외야수)
김도윤 (청주고 투수)
"""

# 함수 호출 및 결과 출력
formatted_list = format_player_data(input_data)
for player_info in formatted_list:
    print(player_info)