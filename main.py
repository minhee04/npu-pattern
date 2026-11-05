import time
import json

def mac(filter_matrix, input_matrix):
    score = 0.0

    for i in range(len(filter_matrix)):
        for j in range(len(filter_matrix[i])):
            score += filter_matrix[i][j] * input_matrix[i][j]

    return score

def validate_matrix(matrix, size):
    if not isinstance(matrix, list) or len(matrix) != size:
        return False

    for row in matrix:
        if not isinstance(row, list) or len(row) != size:
            return False

        for value in row:
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                return False

    return True

def normalize_label(label):
    if label == "+" or label == "Cross" or label == "cross":
        return "Cross"

    if label == "x" or label == "X":
        return "X"

    return "UNDECIDED"


def normalize_filter_keys(filters):
    normalized = {}

    for key, value in filters.items():
        key = str(key).strip().lower()

        if key in ["cross", "+"]:
            normalized["cross"] = value
        elif key in ["x"]:
            normalized["x"] = value

    return normalized


def classify(score_cross, score_x):
    epsilon = 1e-9

    if abs(score_cross - score_x) < epsilon:
        return "UNDECIDED"

    if score_cross > score_x:
        return "Cross"

    return "X"

def measure_mac_time(filter_matrix, input_matrix, repeat=100):
    start = time.perf_counter()

    for _ in range(repeat):
        mac(filter_matrix, input_matrix)

    end = time.perf_counter()

    average_ms = (end - start) / repeat * 1000
    return average_ms

def read_matrix(size, name):
    print(f"{name} 행렬을 입력하세요. (각 행에 숫자 {size}개)")

    matrix = []

    for i in range(size):
        while True:
            try:
                row = input(f"{i + 1}행: ").split()

                if len(row) != size:
                    print(f"숫자를 정확히 {size}개 입력하세요.")
                    continue

                row = [float(value) for value in row]
                matrix.append(row)
                break

            except ValueError:
                print("숫자만 입력할 수 있습니다. 다시 입력하세요.")

    return matrix

def run_user_mode():
    print("\n=== 사용자 입력 모드 ===")

    filter_cross = read_matrix(3, "Cross 필터")
    filter_x = read_matrix(3, "X 필터")

    print("\n필터 입력이 완료되었습니다.")

    input_matrix = read_matrix(3, "입력 패턴")

    start = time.perf_counter()

    score_cross = mac(filter_cross, input_matrix)
    score_x = mac(filter_x, input_matrix)

    end = time.perf_counter()

    result = classify(score_cross, score_x)
    elapsed_ms = (end - start) * 1000

    print("\n=== MAC 연산 결과 ===")
    print(f"Cross 점수: {score_cross}")
    print(f"X 점수: {score_x}")
    
    print(f"실행 시간: {elapsed_ms:.6f} ms")

    display_result = "판정 불가" if result == "UNDECIDED" else result
    print(f"분류 결과: {display_result}")


def load_json_data(filename):
    try:
        with open(filename, "r", encoding="utf-8") as file:
            data = json.load(file)

        return data

    except FileNotFoundError:
        print(f"파일을 찾을 수 없습니다: {filename}")

    except json.JSONDecodeError:
        print("JSON 파일 형식이 올바르지 않습니다.")

    return None

def run_json_mode(filename="data.json"):
    data = load_json_data(filename)

    if data is None:
        return

    if not isinstance(data, dict):
        print("JSON 데이터의 최상위 형식이 올바르지 않습니다.")
        return

    if not isinstance(data.get("filters"), dict):
        print("JSON filters 형식이 올바르지 않습니다.")
        return

    if not isinstance(data.get("patterns"), dict):
        print("JSON patterns 형식이 올바르지 않습니다.")
        return

    total = 0
    passed = 0
    failed = []

    for pattern_id, pattern_data in data["patterns"].items():
        total += 1

        try:
            size = int(pattern_id.split("_")[1])
            filter_key = f"size_{size}"
            
            if filter_key not in data["filters"]:
                raise ValueError(
                    f"필터 데이터 누락: {filter_key} (사용 가능한 키: {list(data['filters'].keys())})"
                )

            filters = data["filters"][filter_key]

            if not isinstance(filters, dict):
                raise ValueError(f"{filter_key} 필터 형식 오류")

            filters = normalize_filter_keys(filters)

            if "cross" not in filters:
                raise ValueError(f"{filter_key}에 Cross 필터가 없습니다.")

            if "x" not in filters:
                raise ValueError(f"{filter_key}에 X 필터가 없습니다.")

            filter_cross = filters["cross"]
            filter_x = filters["x"]



            input_matrix = pattern_data["input"]
            expected = normalize_label(pattern_data["expected"])

            if not validate_matrix(filter_cross, size):
                raise ValueError("Cross 필터 행렬 크기 오류")

            if not validate_matrix(filter_x, size):
                raise ValueError("X 필터 행렬 크기 오류")

            if not validate_matrix(input_matrix, size):
                raise ValueError("입력 패턴 행렬 크기 오류")

            if expected == "UNDECIDED":
                raise ValueError("예상 정답 라벨 오류")

            score_cross = mac(filter_cross, input_matrix)
            score_x = mac(filter_x, input_matrix)

            result = classify(score_cross, score_x)

            status = "PASS" if result == expected else "FAIL"

            print(f"\n[{pattern_id}]")
            print(f"Cross 점수: {score_cross}")
            print(f"X 점수: {score_x}")
            print(f"분류 결과: {result}")
            print(f"예상 정답: {expected}")
            print(f"결과: {status}")

            if status == "PASS":
                passed += 1
            else:
                failed.append((pattern_id, "분류 결과와 예상 정답 불일치"))

        except (KeyError, ValueError, IndexError, TypeError) as error:
            print(f"\n[{pattern_id}]")
            print(f"결과: FAIL - {error}")
            failed.append((pattern_id, str(error)))

    print("\n========== 테스트 요약 ==========")
    print(f"전체 테스트: {total}")
    print(f"PASS: {passed}")
    print(f"FAIL: {len(failed)}")

    if failed:
        print("\n실패한 테스트:")
        for pattern_id, reason in failed:
            print(f"- {pattern_id}: {reason}")

def run_performance_test():
    sizes = [3, 5, 13, 25]
    repeat = 100

    print("\n========== MAC 성능 측정 ==========")
    print(f"{'행렬 크기':<12}{'평균 시간(ms)':<20}{'연산량(N²)'}")

    for size in sizes:
        filter_matrix = [
            [1.0 for _ in range(size)]
            for _ in range(size)
        ]

        input_matrix = [
            [1.0 for _ in range(size)]
            for _ in range(size)
        ]

        average_ms = measure_mac_time(
            filter_matrix,
            input_matrix,
            repeat
        )

        operation_count = size ** 2

        print(
            f"{size}x{size:<10}"
            f"{average_ms:<20.6f}"
            f"{operation_count}"
        )


def main():
    while True:
        print("\n========== Mini NPU Simulator ==========")
        print("1. 사용자 입력 모드")
        print("2. JSON 테스트 모드")
        print("3. 성능 측정")
        print("0. 종료")

        choice = input("메뉴 선택: ")

        if choice == "1":
            run_user_mode()

        elif choice == "2":
            run_json_mode()

        elif choice == "3":
            run_performance_test()

        elif choice == "0":
            print("프로그램을 종료합니다.")
            break

        else:
            print("잘못된 입력입니다. 다시 선택하세요.")


if __name__ == "__main__":
    main()