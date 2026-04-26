<!-- infographic-hero -->
![IEEE 754 Floating-Point Arithmetic Deep Dive 핵심 요약](figures/infographic.svg)

*Figure: IEEE 754 Floating-Point Arithmetic Deep Dive 한 장 요약 인포그래픽*

# IEEE 754 부동소수점 연산 심화: 비트 단위로 이해하는 실수 연산

## 개요

프로그래밍에서 실수(소수점이 있는 수)를 다룰 때, 컴퓨터는 내부적으로 **IEEE 754** 표준에 따라 이진수로 변환하여 저장합니다. `0.1 + 0.2 != 0.3` 같은 유명한 문제도 이 표현 방식에서 비롯됩니다.

이 튜토리얼에서는 IEEE 754 **단정밀도(Single Precision, 32비트)** 부동소수점의 구조를 비트 단위로 분석하고, 덧셈/곱셈/나눗셈 연산이 실제로 어떻게 수행되는지 Python으로 직접 시뮬레이션합니다.

다루는 내용:

1. IEEE 754 32비트 부동소수점의 구조 (부호, 지수, 가수)
2. Python `struct` 모듈을 사용한 비트 변환
3. 부동소수점 덧셈의 단계별 과정
4. 사칙연산(덧셈, 곱셈, 나눗셈) 시뮬레이터 구현

---

## 1. IEEE 754 단정밀도 부동소수점 구조

IEEE 754 단정밀도(32비트) 부동소수점은 다음 세 부분으로 구성됩니다:

```
| 부호(1비트) | 지수(8비트) | 가수(23비트) |
|     S       |  Exponent   |  Mantissa    |
```

- **부호(Sign)**: 0이면 양수, 1이면 음수
- **지수(Exponent)**: 바이어스(bias=127)가 적용된 지수. 실제 지수 = 저장된 지수 - 127
- **가수(Mantissa/Fraction)**: 정규화된 수의 소수 부분. 실제 값은 `1.가수` (hidden bit)

최종 값은 다음 공식으로 계산됩니다:

$$(-1)^S \times 1.\text{Mantissa} \times 2^{\text{Exponent} - 127}$$

---

## 2. 비트 변환 유틸리티 함수 구현

먼저 float와 이진 문자열 사이의 변환 함수를 구현합니다.

```python
import struct

def float_to_bits(f):
    """32비트 float -> 이진 문자열"""
    [d] = struct.unpack(">I", struct.pack(">f", f))
    return f"{d:032b}"

def bits_to_float(bstr):
    """이진 문자열 -> 32비트 float"""
    i = int(bstr, 2)
    [f] = struct.unpack(">f", struct.pack(">I", i))
    return f

def decode_float(bstr):
    """부동소수점 구성요소 추출"""
    sign = int(bstr[0], 2)
    exponent = int(bstr[1:9], 2)
    mantissa = bstr[9:]
    bias = 127
    actual_exp = exponent - bias
    mantissa_val = 1 + sum([int(bit)*2**(-i-1) for i, bit in enumerate(mantissa)])
    return sign, exponent, mantissa_val, actual_exp
```

핵심은 `struct` 모듈의 사용입니다:

- `struct.pack(">f", 0.75)`: float 값을 빅엔디안 4바이트로 패킹
- `struct.unpack(">I", ...)`: 4바이트를 부호 없는 32비트 정수로 해석
- `f"{d:032b}"`: 정수를 32자리 이진 문자열로 변환

예를 들어 `0.75`의 변환 과정을 살펴보겠습니다:

```python
struct.pack(">f", 0.75)  # b'?@\x00\x00'
```

이 바이트를 정수로 해석하면:

```python
[d] = struct.unpack(">I", b'?@\x00\x00')
print(d)  # 1061158912
print(f"{d:032b}")  # '00111111010000000000000000000000'
```

---

## 3. 부동소수점 덧셈 과정 시뮬레이션

0.75 + 0.25 = 1.0을 IEEE 754 연산 과정으로 단계별로 시뮬레이션합니다.

```python
# 두 수의 32비트 표현
a, b = 0.75, 0.25
bits_a = float_to_bits(a)
bits_b = float_to_bits(b)

print("A = 0.75")
print("비트 표현:", bits_a)
print("B = 0.25")
print("비트 표현:", bits_b)
```

<details><summary>Output</summary>

```
A = 0.75
비트 표현: 00111111010000000000000000000000
B = 0.25
비트 표현: 00111110100000000000000000000000
```

</details>

각 비트 표현을 분석해보겠습니다:

**0.75의 비트 분석:**
```
0  01111110  10000000000000000000000
S  Exponent  Mantissa
```
- 부호: 0 (양수)
- 지수: 01111110 = 126, 실제 지수 = 126 - 127 = **-1**
- 가수: 1.1 (hidden bit 포함) = **1.5**
- 값: $1.5 \times 2^{-1} = 0.75$

**0.25의 비트 분석:**
```
0  01111101  00000000000000000000000
S  Exponent  Mantissa
```
- 부호: 0 (양수)
- 지수: 01111101 = 125, 실제 지수 = 125 - 127 = **-2**
- 가수: 1.0 (hidden bit 포함) = **1.0**
- 값: $1.0 \times 2^{-2} = 0.25$

### 덧셈의 4단계 과정

부동소수점 덧셈은 다음 순서로 수행됩니다:

```python
# 각 요소 분리
sign_a, exp_a, mant_a, act_exp_a = decode_float(bits_a)
sign_b, exp_b, mant_b, act_exp_b = decode_float(bits_b)

print("[A 해석]")
print(f"부호: {sign_a}, 지수(실제): {act_exp_a}, 가수: {mant_a}")
print("[B 해석]")
print(f"부호: {sign_b}, 지수(실제): {act_exp_b}, 가수: {mant_b}")
```

<details><summary>Output</summary>

```
[A 해석]
부호: 0, 지수(실제): -1, 가수: 1.5
[B 해석]
부호: 0, 지수(실제): -2, 가수: 1.0
```

</details>

**Step 1 - 지수 정렬(Exponent Alignment):**

두 수의 지수가 다르면, 작은 쪽의 지수를 큰 쪽에 맞춥니다. 이때 가수를 오른쪽으로 시프트합니다.

```python
# 지수 맞추기
if exp_a > exp_b:
    shift = exp_a - exp_b
    mant_b /= 2**shift  # B의 가수를 오른쪽으로 시프트
    exp_res = exp_a
elif exp_b > exp_a:
    shift = exp_b - exp_a
    mant_a /= 2**shift
    exp_res = exp_b
else:
    exp_res = exp_a
```

A의 지수(126)가 B의 지수(125)보다 크므로, B의 가수를 1비트 오른쪽으로 시프트합니다:
- B 가수: 1.0 -> 0.5 (shift 1)
- 결과 지수: 126

**Step 2 - 가수 덧셈:**

```python
mant_res = mant_a + mant_b  # 1.5 + 0.5 = 2.0
```

**Step 3 - 정규화(Normalization):**

가수가 2 이상이면 오른쪽으로 시프트하고 지수를 증가시킵니다.

```python
if mant_res >= 2:
    mant_res /= 2  # 2.0 -> 1.0
    exp_res += 1   # 126 -> 127
```

**Step 4 - 결과 인코딩:**

```python
bias = 127
exp_bits = f"{exp_res:08b}"  # 127 -> '01111111'
mant_bits = ""
m_temp = mant_res - 1  # hidden bit 제거: 1.0 - 1 = 0.0
for i in range(23):
    m_temp *= 2
    bit = int(m_temp)
    mant_bits += str(bit)
    m_temp -= bit

result_bits = f"0{exp_bits}{mant_bits}"
result_value = bits_to_float(result_bits)

print("[연산 과정 요약]")
print(f"정렬 후 가수 합: {mant_a:.6f} + {mant_b:.6f} = {mant_res:.6f}")
print(f"최종 지수: {exp_res}  (bias={bias})")
print(f"결과 비트: {result_bits}")
print(f"IEEE754 해석 값 = {result_value}")
```

<details><summary>Output</summary>

```
[연산 과정 요약]
정렬 후 가수 합: 1.500000 + 0.500000 = 1.000000
최종 지수: 127  (bias=127)

결과 비트: 00111111100000000000000000000000
IEEE754 해석 값 = 1.0
```

</details>

결과 비트 `00111111100000000000000000000000`을 분석하면:
- 부호: 0 (양수)
- 지수: 01111111 = 127, 실제 지수 = 127 - 127 = 0
- 가수: 0 (hidden bit 포함 시 1.0)
- 값: $1.0 \times 2^{0} = 1.0$

정확히 0.75 + 0.25 = 1.0이 나왔습니다.

---

## 4. 사칙연산 시뮬레이터 구현

이제 덧셈뿐 아니라 곱셈, 나눗셈까지 지원하는 완전한 시뮬레이터를 구현합니다.

### 4.1 인코딩 및 정규화 함수

```python
def encode_float(sign, exponent, mantissa):
    """sign, exponent, mantissa -> IEEE754 32비트 문자열"""
    e_bits = f"{exponent:08b}"
    m_val = mantissa - 1  # hidden bit 제거
    m_bits = ""
    for i in range(23):
        m_val *= 2
        bit = int(m_val)
        m_bits += str(bit)
        m_val -= bit
    return f"{sign}{e_bits}{m_bits}"

def normalize(mant, exp):
    """가수를 1.xxx 형태로 정규화"""
    while mant >= 2:
        mant /= 2
        exp += 1
    while mant < 1 and exp > 0:
        mant *= 2
        exp -= 1
    return mant, exp
```

`normalize` 함수는 가수가 $[1.0, 2.0)$ 범위에 오도록 조정합니다. 가수가 2 이상이면 오른쪽으로 시프트(지수 증가), 1 미만이면 왼쪽으로 시프트(지수 감소)합니다.

### 4.2 덧셈, 곱셈, 나눗셈 시뮬레이터

```python
def simulate_add(a, b):
    """덧셈 시뮬레이션"""
    sa, ea, ma, exa = decode_float(float_to_bits(a))
    sb, eb, mb, exb = decode_float(float_to_bits(b))

    # 지수 정렬
    if ea > eb:
        mb /= 2**(ea - eb)
        e_res = ea
    else:
        ma /= 2**(eb - ea)
        e_res = eb

    # 가수 덧셈 (부호 같다고 가정)
    m_res = ma + mb
    m_res, e_res = normalize(m_res, e_res)

    result_bits = encode_float(0, e_res, m_res)
    return bits_to_float(result_bits), result_bits, m_res, e_res

def simulate_mul(a, b):
    """곱셈 시뮬레이션"""
    sa, ea, ma, exa = decode_float(float_to_bits(a))
    sb, eb, mb, exb = decode_float(float_to_bits(b))

    s_res = sa ^ sb             # 부호: XOR
    e_res = ea + eb - 127       # 지수: 더하고 바이어스 빼기
    m_res = ma * mb             # 가수: 곱하기
    m_res, e_res = normalize(m_res, e_res)

    result_bits = encode_float(s_res, e_res, m_res)
    return bits_to_float(result_bits), result_bits, m_res, e_res

def simulate_div(a, b):
    """나눗셈 시뮬레이션"""
    sa, ea, ma, exa = decode_float(float_to_bits(a))
    sb, eb, mb, exb = decode_float(float_to_bits(b))

    s_res = sa ^ sb             # 부호: XOR
    e_res = ea - eb + 127       # 지수: 빼고 바이어스 더하기
    m_res = ma / mb             # 가수: 나누기
    m_res, e_res = normalize(m_res, e_res)

    result_bits = encode_float(s_res, e_res, m_res)
    return bits_to_float(result_bits), result_bits, m_res, e_res
```

각 연산의 핵심 차이를 정리하면:

| 연산 | 부호 | 지수 | 가수 |
|---|---|---|---|
| 덧셈 | 규칙에 따라 결정 | 정렬 후 유지 | 더하기 |
| 곱셈 | XOR (같으면 +, 다르면 -) | 더하고 바이어스 차감 | 곱하기 |
| 나눗셈 | XOR (같으면 +, 다르면 -) | 빼고 바이어스 가산 | 나누기 |

### 4.3 시뮬레이션 실행

0.75와 0.25로 세 가지 연산을 수행합니다.

```python
a, b = 0.75, 0.25
print("===== IEEE 754 부동소수점 연산 시뮬레이터 =====")
print(f"A = {a}, B = {b}")
print("-----------------------------------------------")

# 덧셈
r_add, bits_add, m_add, e_add = simulate_add(a, b)
print("[+] 덧셈 (A + B)")
print(f"가수합 = {m_add:.6f}, 지수 = {e_add}")
print("결과 비트:", bits_add)
print("결과 값 =", r_add)
print("-----------------------------------------------")

# 곱셈
r_mul, bits_mul, m_mul, e_mul = simulate_mul(a, b)
print("[*] 곱셈 (A * B)")
print(f"가수곱 = {m_mul:.6f}, 지수 = {e_mul}")
print("결과 비트:", bits_mul)
print("결과 값 =", r_mul)
print("-----------------------------------------------")

# 나눗셈
r_div, bits_div, m_div, e_div = simulate_div(a, b)
print("[/] 나눗셈 (A / B)")
print(f"가수나눗셈 = {m_div:.6f}, 지수 = {e_div}")
print("결과 비트:", bits_div)
print("결과 값 =", r_div)
```

<details><summary>Output</summary>

```
===== IEEE 754 부동소수점 연산 시뮬레이터 =====
A = 0.75, B = 0.25
-----------------------------------------------
[+] 덧셈 (A + B)
가수합 = 1.000000, 지수 = 127
결과 비트: 00111111100000000000000000000000
결과 값 = 1.0
-----------------------------------------------
[*] 곱셈 (A * B)
가수곱 = 1.500000, 지수 = 124
결과 비트: 00111110010000000000000000000000
결과 값 = 0.1875
-----------------------------------------------
[/] 나눗셈 (A / B)
가수나눗셈 = 1.500000, 지수 = 128
결과 비트: 01000000010000000000000000000000
결과 값 = 3.0
```

</details>

각 연산 결과를 검증해봅시다:

- **덧셈**: 0.75 + 0.25 = **1.0** (정확)
- **곱셈**: 0.75 * 0.25 = **0.1875** (정확)
- **나눗셈**: 0.75 / 0.25 = **3.0** (정확)

모든 연산이 IEEE 754 규칙에 따라 정확하게 수행되었습니다.

---

## 5. 연산별 상세 분석

### 5.1 곱셈 상세 분석 (0.75 * 0.25 = 0.1875)

곱셈 과정을 단계별로 풀어보겠습니다:

1. **부호**: 0 XOR 0 = 0 (양수)
2. **지수**: 126 + 125 - 127 = **124**
   - 실제 지수: 124 - 127 = **-3**
3. **가수**: 1.5 * 1.0 = **1.5** (정규화 불필요)
4. **결과**: $1.5 \times 2^{-3} = 1.5 \times 0.125 = 0.1875$

### 5.2 나눗셈 상세 분석 (0.75 / 0.25 = 3.0)

1. **부호**: 0 XOR 0 = 0 (양수)
2. **지수**: 126 - 125 + 127 = **128**
   - 실제 지수: 128 - 127 = **1**
3. **가수**: 1.5 / 1.0 = **1.5** (정규화 불필요)
4. **결과**: $1.5 \times 2^{1} = 1.5 \times 2 = 3.0$

---

## 결론

이 튜토리얼에서는 IEEE 754 부동소수점 연산의 내부 동작을 비트 수준에서 살펴보았습니다. 핵심 내용을 정리하면:

1. **부동소수점 구조**: 32비트를 부호(1) + 지수(8) + 가수(23)로 나누어 실수를 표현
2. **덧셈**: 지수 정렬 -> 가수 덧셈 -> 정규화 -> 반올림
3. **곱셈**: 부호 XOR, 지수 덧셈(바이어스 차감), 가수 곱셈
4. **나눗셈**: 부호 XOR, 지수 뺄셈(바이어스 가산), 가수 나눗셈

이 지식은 다음과 같은 실무 상황에서 유용합니다:

- **수치 안정성 디버깅**: 딥러닝 학습 중 NaN이나 Inf가 발생할 때 원인 파악
- **혼합 정밀도 학습 이해**: FP16/BF16과 FP32의 차이를 이해하고 적절히 활용
- **양자화 기법 이해**: INT8 양자화에서 Scale/Zero-point 계산의 배경 지식
- **정밀도 손실 예측**: 큰 수와 작은 수를 더할 때 발생하는 정밀도 손실 원리 파악

---

## 참고 자료

- [IEEE 754 Wikipedia](https://en.wikipedia.org/wiki/IEEE_754)
- [What Every Computer Scientist Should Know About Floating-Point Arithmetic](https://docs.oracle.com/cd/E19957-01/806-3568/ncg_goldberg.html)
- [Python struct 모듈 문서](https://docs.python.org/3/library/struct.html)
- [Float Exposed - 부동소수점 시각화 도구](https://float.exposed/)