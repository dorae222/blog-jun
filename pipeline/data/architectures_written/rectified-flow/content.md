# Rectified Flow: 직선 궤적 기반 생성 흐름 프레임워크

**UT Austin / Peking University** · **2022-09-07** · **Diffusion** · **Apache 2.0**

## 개요

Rectified Flow는 2022년 UT Austin과 Peking University의 Xingchao Liu, Chengyue Gong, Qiang Liu가 제안한 생성 모델 프레임워크로, 노이즈 분포 $\pi_0$와 데이터 분포 $\pi_1$ 사이의 전송 경로를 직선화(rectification)하여 최적 수송(Optimal Transport) 경로에 근사하는 방법이다.

확산 모델의 핵심 과제 중 하나는 샘플링 효율이다. DDPM이나 Score-SDE에서 학습하는 확산 경로는 곡선 형태를 띠므로, ODE 적분기가 이 곡선을 정확히 따라가려면 많은 스텝(NFE, Number of Function Evaluations)이 필요하다. 경로가 직선에 가까울수록 단순한 오일러 방법으로도 정확한 샘플링이 가능해지며, 이론적 극한에서는 단 1스텝만으로 완벽한 샘플링이 달성된다.

Rectified Flow의 핵심 아이디어는 매우 단순하다: 독립적으로 샘플링된 노이즈 $X_0 \sim \pi_0$와 데이터 $X_1 \sim \pi_1$ 쌍을 선분으로 연결하는 직선 보간 경로 $X_t = (1-t)X_0 + tX_1$을 학습 목표로 삼고, 이 직선을 따르는 벡터 필드 $v(X_t, t) \approx X_1 - X_0$를 신경망으로 근사한다. 이 단순한 설정이 강력한 생성 모델을 만드는 이유는, 직선 경로가 ODE 적분의 수치 오차를 최소화하기 때문이다.

실제로 독립 커플링에서 시작하면 경로가 교차하여 완벽한 직선이 되지 않지만, **Reflow** 과정--현재 모델로 커플링을 재생성 후 재학습--을 반복하면 경로가 점점 직선에 수렴한다. Rectified Flow는 수학적으로 Flow Matching의 OT-CFM(Optimal Transport Conditional Flow Matching)과 동치이며, Stable Diffusion 3, FLUX.1 등 현대 대규모 생성 모델들이 채택한 Flow Matching의 이론적 기반이 되었다.

![1-Rectified Flow와 2-Rectified Flow의 이미지 생성 결과 — 스텝 수에 따른 생성 품질 비교](figures/fig_1.jpg)
*Figure 1: Rectified Flow의 이미지 생성 궤적 — 1-Rectified Flow는 N=2 이상에서 양호한 결과를 보이고, 2-Rectified Flow(Reflow 1회 적용)는 거의 직선 궤적을 형성하여 N=1(단일 스텝)에서도 고품질 샘플을 생성한다. (Source: Liu et al., 2022)*

![Rectified Flow 아키텍처 — 노이즈-데이터 직선 보간 경로와 Reflow 재학습 기반 생성 흐름 구조](figures/architecture.svg)

*Figure 2: Rectified Flow 아키텍처 — 노이즈와 데이터 쌍을 선형 보간 경로로 연결하고 벡터 필드를 학습하며, Reflow 과정으로 경로를 직선에 수렴시켜 단일 스텝 생성을 가능하게 한다.*

## 아키텍처 상세

### 직선 보간 경로 정의

Rectified Flow의 경로는 시간 $t \in [0, 1]$에서의 선형 보간으로 정의된다:

$$X_t = (1-t)X_0 + tX_1, \quad X_0 \sim \pi_0, \quad X_1 \sim \pi_1$$

이 경로의 시간 미분은 상수 벡터 $\dot{X}_t = X_1 - X_0$이므로, 이상적으로는 경로를 따르는 벡터 필드도 상수가 되어 단일 오일러 스텝으로 $X_0$에서 $X_1$에 도달할 수 있다.

### 학습 목표 함수

신경망 $v_\theta$는 다음 회귀 손실을 최소화하여 벡터 필드를 학습한다:

$$\mathcal{L}(\theta) = \int_0^1 \mathbb{E}_{(X_0, X_1)}\left[\|v_\theta(X_t, t) - (X_1 - X_0)\|^2\right]dt$$

여기서 $t \sim \mathcal{U}[0,1]$로 균일 샘플링하며, $(X_0, X_1)$는 독립적으로 샘플링된 커플링이다. 이 손실은 Score Matching 손실과 밀접한 관련이 있으며, Flow Matching의 조건부 흐름 매칭 목표와 수학적으로 동치이다.

### Reflow 알고리즘: 경로 직선화

![Rectified Flow의 경로 직선화 과정 — (a) 교차하는 선형 보간 경로, (b) 교차점에서 재배선된 궤적](figures/fig_2_1.png)
*Figure 2(a): 선형 보간의 경로 교차 — 독립 커플링 $(X_0, X_1) \sim \pi_0 \times \pi_1$의 직선 보간 경로가 서로 교차하는 모습. Rectified Flow는 이 교차점에서 궤적을 재배선하여 비교차 특성을 달성한다. (Source: Liu et al., 2022)*

1-Rectified Flow에서 학습된 벡터 필드 $v_\theta$로 ODE $dZ_t = v_\theta(Z_t, t)dt$를 풀면 커플링 $(Z_0, Z_1)$을 생성할 수 있다. 이 커플링은 독립 커플링보다 더 "정렬"되어 있으므로, 이를 새로운 학습 데이터로 사용하여 2-Rectified Flow를 학습하면 경로가 더욱 직선화된다:

$$\text{Reflow: } (Z_0, Z_1) \leftarrow \text{ODE}(v_\theta), \quad v_{\theta'} \leftarrow \arg\min \mathbb{E}\left[\|v_{\theta'}(Z_t, t) - (Z_1 - Z_0)\|^2\right]$$

이 과정을 반복하면 경로의 곡률(curvature)이 점차 줄어들어, 최종적으로 단 1~2 스텝으로 고품질 샘플을 생성할 수 있다.

### 비교차 특성과 최적 수송

![Reflow 반복에 따른 궤적 직선화 과정 — 토이 예제에서 Reflow 단계별 궤적 변화](figures/fig_3_1.png)
*Figure 3(a): Reflow에 의한 궤적 직선화 — 토이 예제에서 보라색 점($\pi_0$)과 빨간색 점($\pi_1$) 사이의 궤적이 Reflow 반복에 따라 점차 직선에 수렴하며, 수송 비용이 최적 수송에 근접한다. (Source: Liu et al., 2022)*

학습된 흐름은 **비교차 특성(non-crossing property)**을 가진다: 서로 다른 초기점에서 출발한 궤적이 교차하지 않는다. 이 특성은 수송 비용 $\mathbb{E}[\|X_1 - X_0\|^2]$를 자연스럽게 최소화하는 방향으로 작용하며, Reflow를 반복할수록 최적 수송 맵에 수렴한다는 이론적 보장이 존재한다.

![Rectified Flow와 VP ODE, sub-VP ODE의 궤적 비교 — 직선 경로 학습의 효과](figures/fig_4_1.png)
*Figure 4: Rectified Flow vs VP/sub-VP ODE — Rectified Flow는 1회 Reflow로 거의 직선 궤적을 달성하지만, VP ODE와 sub-VP ODE는 곡선 궤적을 형성하며 Reflow로도 직선화가 불가능하다. (Source: Liu et al., 2022)*

## 핵심 혁신

Rectified Flow의 핵심 혁신은 직선 경로 학습이라는 단순하지만 강력한 아이디어를 통해 확산 모델의 샘플링 효율을 이론적 한계까지 끌어올린 것이다. DDPM/DDIM 계열이 곡선 궤적을 따라 많은 스텝이 필요한 반면, Rectified Flow는 직선 궤적을 학습하여 1~2 스텝 생성을 가능하게 한다. Reflow의 반복적 직선화는 증류(distillation) 없이도 경로를 최적화하는 자기 개선적(self-improving) 방법이며, 이는 Consistency Distillation과 상보적인 접근법이다. Flow Matching과의 수학적 동치성은 두 독립적 연구가 같은 최적 해에 도달했음을 보여주는 이론적 성과이다.

## 벤치마크/성능

| 모델 | 데이터셋 | NFE | FID (↓) | IS (↑) |
|------|---------|-----|---------|--------|
| 1-Rectified Flow | CIFAR-10 | 127 | 2.58 | 9.60 |
| 2-Rectified Flow + 증류 | CIFAR-10 | 1 | 4.85 | 9.01 |
| DDIM | CIFAR-10 | 10 | 13.36 | - |
| DDIM | CIFAR-10 | 50 | 4.67 | 8.78 |
| DDPM | CIFAR-10 | 1000 | 3.17 | 9.46 |
| 1-Rectified Flow | LSUN Bedroom | 110 | 3.38 | - |

동일 NFE 예산에서 Rectified Flow가 DDIM보다 일관되게 낮은 FID를 달성한다. 2-Rectified Flow + 증류 조합은 단 1 스텝으로 FID 4.85를 달성하여, 1000 스텝 DDPM에 근접하는 품질을 보인다.

## 학습

실험은 CIFAR-10(32x32)과 LSUN-Bedroom(256x256)에서 수행되었다. 노이즈 분포는 $\pi_0 = \mathcal{N}(0, I)$, 데이터 분포는 $\pi_1$이다. 백본 네트워크로 U-Net 아키텍처를 사용하며, 독립 커플링 $(X_0, X_1)$에서 $t \sim \mathcal{U}[0,1]$로 시간을 샘플링하여 학습한다. Flow Matching 논문(Lipman et al., 2022)과 동시에 독립적으로 발표되었으며, 두 방법이 수학적으로 동치임이 이후 연구에서 확인되었다.

## 관련 모델

Rectified Flow는 Flow Matching의 이론적 변형이며, Stable Diffusion 3, FLUX.1 등이 이 프레임워크를 채택하였다. Consistency Model(OpenAI)은 유사한 목적의 증류 기법으로, Reflow와 상보적으로 활용 가능하다. InstaFlow는 Rectified Flow의 Reflow를 대규모 텍스트-이미지 모델에 적용한 후속 연구이다.

## 참고 자료

- [논문: Flow Straight and Fast: Learning to Generate and Transfer Data with Rectified Flow](https://arxiv.org/abs/2209.03003)
- [코드](https://github.com/gnobitab/RectifiedFlow)

## 관련 문서

- [[flow-matching|Flow Matching]] — 변형 원본