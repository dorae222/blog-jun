## 개요

Flow Matching(FM)은 Lipman et al.이 ICLR 2023에서 제안한 생성 모델 학습 프레임워크로, 연속 정규화 플로우(Continuous Normalizing Flows, CNF)를 **시뮬레이션 없이** 효율적으로 학습하는 방법이다. 기존 CNF 학습은 ODE 적분을 통한 시뮬레이션이 필요해 계산 비용이 컸지만, Flow Matching은 조건부 확률 경로를 활용해 이 문제를 우회한다. 특히 최적 수송(Optimal Transport, OT) 경로를 적용하면 노이즈에서 데이터까지의 궤적이 직선에 가까워져 적은 함수 평가 횟수(NFE)로도 고품질 샘플링이 가능하다. 이 방법론은 이후 Stable Diffusion 3, Flux 등 최신 대규모 이미지 생성 모델의 이론적 기반이 되었다.

다음은 Flow Matching(OT 경로)으로 학습한 CNF가 생성한 ImageNet 128x128 샘플로, 시뮬레이션 없는 학습만으로도 다양하고 사실적인 이미지를 생성할 수 있음을 보여준다.

![Flow Matching OT 경로로 생성한 ImageNet 128x128 샘플](figures/fig_1.png)
*Figure 1: Flow Matching(OT 경로)으로 학습한 CNF의 ImageNet 128x128 무조건부 생성 샘플 ( 동물, 사물, 풍경 등 다양한 카테고리에서 높은 품질의 이미지를 생성한다. (Lipman et al., 2023)*

## 배경 및 문제

### 연속 정규화 플로우 (CNF)

연속 정규화 플로우는 시간 $t \in [0, 1]$에 따라 변화하는 벡터 필드 $v_t : \mathbb{R}^d \to \mathbb{R}^d$를 이용해 ODE를 정의한다.

$$\frac{d}{dt}\psi_t(x) = v_t(\psi_t(x)), \quad \psi_0(x) = x$$

이 플로우 $\psi_t$는 단순한 기저 분포(예: 가우시안 $p_0 = \mathcal{N}(0, I)$)를 복잡한 데이터 분포 $p_1 = q$로 변환한다. 샘플링 시에는 $x_0 \sim p_0$을 샘플링한 뒤 ODE를 수치적으로 적분하여 $x_1 = \psi_1(x_0)$을 얻는다.

핵심적인 성질은 **확률 밀도의 보존**이다. 플로우 $\psi_t$에 의해 밀도가 어떻게 변화하는지를 연속 방정식(continuity equation)으로 기술할 수 있다.

$$\frac{\partial}{\partial t} p_t(x) + \nabla \cdot (p_t(x) v_t(x)) = 0$$

이 방정식이 만족되면, 벡터 필드 $v_t$는 확률 밀도 경로 $p_t$를 **생성(generate)**한다고 말한다. 즉, 임의의 시점 $t$에서 $\psi_t$를 통해 변환된 샘플의 분포가 정확히 $p_t$가 된다.

### 기존 방법의 한계

CNF를 학습하는 기존 방법(FFJORD 등)은 훈련 중에도 ODE 시뮬레이션이 필요해 다음과 같은 문제를 안고 있었다.

- **계산 비용**: ODE 적분은 역전파와 결합되어 메모리 및 시간 비용이 매우 크다. 특히 adaptive solver를 사용하면 학습 스텝당 수백 번의 함수 평가가 필요하다.
- **고차원 비효율성**: 이미지처럼 고차원 데이터에서는 Hutchinson trace estimator의 분산이 커져 사실상 적용이 어렵다.
- **불안정한 학습**: 시뮬레이션 오차가 역전파를 통해 누적되며 학습이 불안정해질 수 있다.

확산 모델(Diffusion Models)은 이 문제를 일부 해결했지만, DDPM의 코사인/분산 스케줄 경로는 곡률이 크고 NFE가 수백 단계에 달하는 경우가 많다. Flow Matching은 이 두 가지 문제를 동시에 해결하고자 한다.

## 핵심 아이디어

Flow Matching의 핵심은 **주변 벡터 필드(marginal vector field)** $u_t(x)$를 직접 회귀하는 대신, 개별 데이터 포인트 $x_1$에 조건화된 **조건부 벡터 필드(conditional vector field)** $u_t(x|x_1)$를 학습하는 것이다. 이 전환이 왜 가능한지를 이해하려면, 먼저 주변 벡터 필드와 조건부 벡터 필드의 관계를 살펴볼 필요가 있다.

### Flow Matching (FM) 손실

이상적으로는 신경망 $v_\theta(x, t)$가 주변 벡터 필드 $u_t(x)$를 근사하도록 학습하면 된다.

$$\mathcal{L}_{FM}(\theta) = \mathbb{E}_{t, p_t(x)}\left[\|v_\theta(x,t) - u_t(x)\|^2\right]$$

그런데 $u_t(x)$는 전체 데이터 분포에 대한 적분을 포함하여 **직접 계산이 불가능(intractable)** 하다. 구체적으로, 주변 벡터 필드는 모든 데이터 포인트에 대한 조건부 벡터 필드의 가중 평균으로 정의된다.

$$u_t(x) = \frac{\int u_t(x|x_1) p_t(x|x_1) q(x_1)\, dx_1}{p_t(x)}$$

이 적분은 데이터 분포 $q(x_1)$ 전체에 대해 수행해야 하므로 closed-form 계산이 불가능하다.

### Conditional Flow Matching (CFM) ) 핵심 통찰

논문의 핵심 기여는 조건부 손실로의 전환이다.

$$\mathcal{L}_{CFM}(\theta) = \mathbb{E}_{t, q(x_1), p_t(x|x_1)}\left[\|v_\theta(x,t) - u_t(x|x_1)\|^2\right]$$

**Theorem 1** (Lipman et al., 2023): $\mathcal{L}_{FM}$과 $\mathcal{L}_{CFM}$은 $\theta$에 대해 **동일한 기울기**를 가진다.

$$\nabla_\theta \mathcal{L}_{FM}(\theta) = \nabla_\theta \mathcal{L}_{CFM}(\theta)$$

증명의 핵심 아이디어는 조건부 기대값의 탑 법칙(tower property)에 있다. CFM 손실을 전개하면 $\theta$에 의존하는 항($v_\theta$를 포함하는 교차항)이 FM 손실과 동일하게 나타나며, 나머지 차이는 $\theta$와 무관한 상수항이다. 따라서 기울기가 동일해진다.

이 정리 덕분에 tractable한 조건부 목표로 intractable한 주변 목표를 대체할 수 있다. 각 학습 스텝에서 $x_1 \sim q$를 샘플링하고, 해당 $x_1$에 조건화된 경로 위의 점 $x \sim p_t(x|x_1)$을 샘플링하면 ODE 시뮬레이션 없이 학습이 가능하다.

## 방법론

### 조건부 확률 경로 설계

가우시안 조건부 경로를 다음과 같이 정의한다.

$$p_t(x|x_1) = \mathcal{N}(x \mid \mu_t(x_1),\, \sigma_t^2 I)$$

여기서 평균과 표준편차는 시간에 따라 선형적으로 변화한다.

$$\mu_t(x_1) = t x_1, \qquad \sigma_t = 1 - (1 - \sigma_{\min})t$$

$t=0$일 때 $\mathcal{N}(0, I)$, $t=1$일 때 $\mathcal{N}(x_1, \sigma_{\min}^2 I)$으로 수렴한다. $\sigma_{\min}$은 매우 작은 값(예: $10^{-5}$)으로 설정한다.

이 설계가 갖는 의미는 다음과 같다. $t=0$에서 소스 분포(순수 가우시안 노이즈)로 시작하여, 시간이 흐르면서 평균은 데이터 포인트 $x_1$을 향해 이동하고 분산은 점차 줄어든다. $t=1$에 도달하면 사실상 $x_1$에 집중된 델타 분포에 가까워진다.

### Diffusion 경로 vs OT 경로 비교

논문에서 가장 중요한 기여 중 하나는 확률 경로의 선택이 학습 효율과 샘플링 품질에 미치는 영향을 분석한 것이다. 다음 그림은 Diffusion 경로와 OT 경로에서 가우시안 소스 분포(왼쪽 아래, $p_0$)로부터 데이터 포인트(오른쪽 위, $x_1$)까지의 궤적을 비교한다.

![Diffusion 경로의 곡선 궤적](figures/p06_fig01.png)
*Diffusion 경로: 가우시안 소스 $p_0$(검정 사각형)에서 데이터 포인트 $x_1$(검정 원)까지의 궤적이 큰 곡률을 가진다. 서로 다른 초기점에서 출발한 궤적들이 복잡하게 휘어지며, 이로 인해 ODE 적분 시 많은 함수 평가 횟수(NFE)가 필요하다.*

![OT 경로의 직선 궤적](figures/p06_fig02.png)
*OT 경로: 동일한 소스와 타겟에 대해 궤적이 거의 직선이다. 곡률이 0에 가까워 단 몇 단계의 Euler 적분만으로도 정확한 샘플링이 가능하다.*

Diffusion 경로에서는 노이즈 스케줄에 의해 궤적이 크게 휘어진다. 이는 시간 초기에 분산이 급격히 변하면서 샘플이 멀리 확산되었다가 나중에 데이터 포인트로 수렴하기 때문이다. 반면 OT 경로는 소스에서 타겟까지 일정한 속도로 직진하므로 수치 적분 오차가 최소화된다.

### OT-CFM: 최적 수송 경로 (직선 궤적)

$x_0 \sim \mathcal{N}(0, I)$와 $x_1 \sim q$를 독립적으로 쌍으로 지을 때 얻어지는 **최적 수송 경로**는 직선이다.

$$x_t = (1-t)x_0 + t x_1$$

이 선형 보간에 대한 조건부 벡터 필드는 단순히 방향 벡터가 된다.

$$u_t(x|x_1) = x_1 - x_0$$

이는 시간에 독립적인 상수 벡터로, 궤적의 곡률이 0이다. 실제 데이터와 노이즈 쌍 $(x_0, x_1)$에 대해 벡터 필드가 단순한 방향만 가리키면 되므로 학습 신호가 매우 명확해진다.

이를 Diffusion 경로의 조건부 벡터 필드와 비교하면 차이가 더 명확하다. VP-SDE(DDPM) 경로에서는 $u_t(x|x_1) = \frac{\dot{\sigma}_t}{\sigma_t}(x - \mu_t) + \dot{\mu}_t$로 시간에 복잡하게 의존하는 반면, OT 경로에서는 상수로 단순화된다.

경로 선택의 효과는 2D checkerboard 데이터에서 더욱 직관적으로 확인할 수 있다. 아래는 Score-Diffusion과 FM-OT가 가우시안 소스에서 checkerboard 분포를 학습하는 과정을 시각화한 것이다.

![Score-Diffusion의 2D checkerboard 궤적 진화](figures/fig_15_1.png)
*Figure 2: Score-Diffusion(SM-Dif)의 checkerboard 학습 궤적 ( 시간이 흐르면서 천천히 패턴이 형성되며, 중간 단계에서 분포가 불안정하게 변화한다. (Lipman et al., 2023)*

![FM-OT의 2D checkerboard 궤적 진화](figures/fig_15_11.png)
*Figure 3: FM-OT의 checkerboard 학습 궤적 ) OT 경로는 초기부터 빠르게 checkerboard 패턴을 형성하며, 안정적이고 효율적인 분포 변환을 수행한다. (Lipman et al., 2023)*

### 학습 알고리즘 요약

OT-CFM의 학습 과정은 놀라울 정도로 간단하다.

1. 데이터 배치 $x_1 \sim q$를 샘플링
2. 소스 노이즈 $x_0 \sim \mathcal{N}(0, I)$를 샘플링
3. 시간 $t \sim \text{Uniform}(0, 1)$을 샘플링
4. 중간점 $x_t = (1-t)x_0 + tx_1$ 계산
5. 신경망 예측 $v_\theta(x_t, t)$와 목표 벡터 $(x_1 - x_0)$ 사이의 MSE 손실 계산
6. 역전파 및 파라미터 업데이트

기존 확산 모델의 노이즈 예측 학습과 형식적으로 매우 유사하지만, 학습 목표가 노이즈가 아닌 **방향 벡터**라는 점이 다르다. DDPM에서 $\epsilon$-예측이 $\epsilon_\theta(x_t, t) \approx \epsilon$인 것에 대응하여, FM-OT에서는 $v_\theta(x_t, t) \approx x_1 - x_0$이다.

### 샘플링

학습 완료 후 샘플링은 ODE 수치 적분으로 수행한다.

1. $x_0 \sim \mathcal{N}(0, I)$ 샘플링
2. Euler 또는 Runge-Kutta 방법으로 $\frac{dx}{dt} = v_\theta(x, t)$ 적분
3. $x_1 = x_0 + \int_0^1 v_\theta(x_t, t)\, dt$

OT 경로는 직선이므로 단 몇 단계(NFE=5~10)로도 충분히 수렴한다.

## 실험 결과

### 훈련 효율성 비교

다음 그림은 ImageNet 64x64에서 훈련 에폭에 따른 FID 변화를 보여준다.

![훈련 중 이미지 품질(FID) 변화](figures/fig_16.png)
*ImageNet 64x64에서 훈련 에폭별 FID 비교. FM-OT(주황)는 ScoreFlow(녹색), FM-Diffusion(파랑), SM-Diffusion(회색) 대비 빠르게 수렴하며, 최종 FID도 가장 낮다. DDPM(검정)도 좋은 성능을 보이지만 1000 NFE가 필요하다.*

FM-OT는 약 100 에폭 이후부터 다른 방법들을 확실히 앞서기 시작하며, 최종적으로 가장 낮은 FID에 도달한다. 특히 ScoreFlow는 초기에 FID가 크게 요동치는 반면, FM 계열은 안정적으로 하강하는 것이 특징적이다.

### 함수 평가 횟수(NFE) 비교

OT 경로의 가장 큰 실용적 장점은 샘플링 시 필요한 함수 평가 횟수(NFE)의 감소이다. 다음 그림은 CIFAR-10에서 훈련 과정 중 adaptive solver(dopri5)가 요구하는 NFE를 비교한다.

![훈련 중 NFE 비교](figures/fig_30.png)
*CIFAR-10에서 훈련 에폭별 NFE 비교 (dopri5 solver, tolerance $10^{-5}$). score\_dif(녹색)는 초기에 1000 이상의 NFE가 필요하지만, fm\_ot(주황)는 전 구간에서 50 내외의 안정적인 NFE를 유지한다. fm\_dif(파랑)도 100 이하로 비교적 효율적이다.*

score\_dif 방법은 학습 초기에 1000 NFE 이상을 요구하다가 점차 감소하지만 500 에폭 후에도 100 전후를 유지한다. 반면 FM-OT는 학습 전 구간에서 50 내외의 극히 낮은 NFE를 보여, OT 경로가 수치 적분 관점에서 얼마나 효율적인지를 잘 보여준다.

### 이미지 생성 (ImageNet 64x64)

| 방법 | NFE | FID ($\downarrow$) |
|------|-----|--------------------|
| DDPM | 1000 | 3.26 |
| DDIM | 100 | 4.67 |
| Flow Matching (Gaussian) | 100 | 3.08 |
| **OT-CFM** | **10** | **3.25** |

다음 그래프는 NFE에 따른 수치 적분 오차를 비교한 것으로, FM-OT가 적은 NFE에서도 현저히 낮은 오차를 달성함을 보여준다.

![NFE에 따른 수치 적분 오차 비교](figures/fig_21_1.png)
*Figure 4: ImageNet 32x32에서 NFE에 따른 수치 적분 오차 ( FM-OT(녹색)는 SM-Dif(파랑) 및 FM-Dif(주황) 대비 모든 NFE 구간에서 현저히 낮은 오차를 보인다. NFE=10에서도 다른 방법의 NFE=100 수준 오차를 달성한다. (Lipman et al., 2023)*

OT-CFM은 DDPM의 1/100 NFE로 비슷한 FID를 달성한다. 이는 직선 경로가 곡선 경로에 비해 수치 적분 오차가 작기 때문이다. 특히 NFE=10이라는 것은 단 10번의 신경망 forward pass만으로 샘플 하나를 생성할 수 있음을 의미하며, 이는 실시간 생성에 매우 유리한 조건이다.

FM-Gaussian이 NFE=100에서 가장 낮은 FID(3.08)를 달성하는 것도 주목할 만하다. 이는 충분한 NFE가 확보되면 Gaussian 경로도 높은 품질을 낼 수 있지만, NFE가 제한되는 실용적 환경에서는 OT 경로가 압도적으로 유리함을 보여준다.

### 단백질 구조 및 기타 모달리티

Flow Matching은 이미지에 국한되지 않으며, 단백질 백본 구조 생성(FoldFlow), 분자 생성(FrameDiff) 등 $SE(3)$ 리 군 위의 기하학적 데이터에도 자연스럽게 확장된다. 이는 Flow Matching의 프레임워크가 유클리드 공간에 특화된 것이 아니라, 일반적인 확률 경로 개념에 기반하기 때문이다. 비유클리드 공간에서의 Riemannian Flow Matching으로 이어지는 이론적 기반이 된다.

## 의의 및 한계

### 의의

- **시뮬레이션-프리 학습**: ODE 적분 없이 단순 회귀로 CNF를 학습, 고차원(이미지 등)으로 확장 가능. FFJORD가 MNIST 수준에 머물렀던 것과 달리 ImageNet 128x128까지 확장에 성공했다.
- **수학적 엄밀성**: FM과 CFM의 기울기 동치(Theorem 1)를 증명, 조건부 목표 사용의 이론적 정당성 확보. 이는 단순한 휴리스틱이 아닌 수학적으로 보장된 대체이다.
- **OT 직선 경로**: NFE 대폭 감소(1000 → 10) → 실용적 초고속 샘플러 구현 가능. 동일 품질 대비 100배 빠른 샘플링.
- **범용성**: 이미지, 오디오, 단백질, 분자, 비디오 등 다양한 도메인 적용 성공.
- **후속 영향**: Stable Diffusion 3의 Rectified Flow, Flux의 이론적 기초가 됨. 현재 대부분의 최신 생성 모델이 Flow Matching 또는 그 변형을 채택하고 있다.

### 한계

- **독립 쌍 가정**: OT-CFM은 $x_0$와 $x_1$을 독립적으로 쌍을 짓는다. 이는 진정한 최적 수송 계획이 아니라, 조건부 수준에서의 OT 경로만 사용하는 것이다. 미니배치 OT(Entropic OT 등)는 더 나은 경로를 제공하지만 구현이 복잡하다(Tong et al., 2023에서 개선).
- **단순 가우시안 소스**: 기저 분포로 가우시안만 고려; 구조화된 사전 지식을 활용하려면 추가 작업이 필요하다. 예를 들어, 이미지 편집에서는 가우시안이 아닌 조건부 분포를 소스로 사용하는 것이 자연스럽다.
- **조건부 생성**: 클래스 조건부, 텍스트 조건부 생성을 위한 classifier-free guidance 통합은 후속 연구에서 다루어졌다. 본 논문은 무조건부(unconditional) 생성에 초점을 맞추고 있다.
- **이론과 실제의 간극**: 조건부 OT 경로가 주변(marginal) 수준에서 최적이라는 보장은 없다. 개별 $(x_0, x_1)$ 쌍에 대해서는 직선이지만, 전체 분포 수준에서의 궤적은 여전히 교차할 수 있다.

## 코드 예제

```python
import torch
import torch.nn as nn

def sample_ot_path(x0: torch.Tensor, x1: torch.Tensor, t: torch.Tensor):
    """OT-CFM 선형 보간: x_t = (1-t)*x0 + t*x1"""
    # t: (B, 1, 1, 1) 형태로 브로드캐스팅
    t_bc = t.view(-1, *([1] * (x0.dim() - 1)))
    xt = (1 - t_bc) * x0 + t_bc * x1
    # 조건부 벡터 필드: 상수 방향 (x1 - x0)
    ut = x1 - x0
    return xt, ut


def train_step(
    model: nn.Module,
    x1: torch.Tensor,          # 실제 데이터 배치
    optimizer: torch.optim.Optimizer,
):
    """Flow Matching (OT-CFM) 단일 학습 스텝"""
    B = x1.size(0)
    device = x1.device

    # 1) 소스 노이즈 샘플링
    x0 = torch.randn_like(x1)

    # 2) 시간 t ~ Uniform(0, 1) 샘플링
    t = torch.rand(B, device=device)

    # 3) OT 선형 경로 위의 중간 점과 목표 벡터 필드 계산
    xt, ut = sample_ot_path(x0, x1, t)

    # 4) 신경망으로 벡터 필드 예측
    vt_pred = model(xt, t)  # v_theta(x_t, t)

    # 5) CFM 손실: ||v_theta(x_t, t) - u_t(x_t | x_1)||^2
    loss = ((vt_pred - ut) ** 2).mean()

    optimizer.zero_grad()
    loss.backward()
    optimizer.step()
    return loss.item()


@torch.no_grad()
def sample(model: nn.Module, shape: tuple, n_steps: int = 10, device="cuda"):
    """Euler 방법으로 ODE 적분 → 샘플 생성"""
    x = torch.randn(*shape, device=device)
    dt = 1.0 / n_steps
    for i in range(n_steps):
        t = torch.full((shape[0],), i * dt, device=device)
        x = x + model(x, t) * dt
    return x
```

## 관련 문서

- [Rectified Flow (Liu et al., 2022)](../rectified-flow/) ) 독립적으로 제안된 유사한 직선 경로 아이디어
- [Stable Diffusion 3 (Esser et al., 2024)](../stable-diffusion-3/) ( Flow Matching을 대규모 텍스트-이미지 생성에 적용
- [Riemannian Flow Matching (Chen & Lipman, 2023)](../riemannian-flow-matching/) ) 비유클리드 다양체로의 확장
- [Conditional Flow Matching (Tong et al., 2023)](../cfm-improved/) ( 미니배치 OT를 활용한 개선
- [DDPM (Ho et al., 2020)](../ddpm/) ) 비교 대상이 되는 기준 확산 모델