# AI tells: worked examples

Tier 3 of the polish skill. Section numbers match the checklist in `ai-tells.md`. Load this only when a call is genuinely close; the cues in the checklist settle most of them.

**Read this first.** Every After below stays inside what its Before already claims. That is the rule the examples are teaching, not an accident of how they were written. When a tell hides the fact that the sentence has nothing to say, the fix is to cut the sentence or ask the writer for the missing detail, never to supply one. A few of the pairs show that outcome directly.

---

## A. Staging instead of stating

### 1. X가 아니라 Y / not X but Y

The negative half names a position nobody took, which makes the positive half sound larger than it is.

**Before (KO):**
> 이것은 단순한 기능 추가가 아니라, 화면 흐름 전체를 다시 설계하는 일이다.

**After (KO):**
> 이번 작업에서 화면 흐름 전체를 다시 설계했다.

**Before (KO, split across two sentences):**
> 이 말이 모든 선택이 같다는 뜻은 아니다. 어떤 선택이 옳은지 확인해 줄 외부 기준이 없다는 뜻이다.

**After (KO):**
> 선택마다 결과는 다르지만, 어느 쪽이 옳은지 확인해 줄 외부 기준은 없다.

**Before (EN):**
> It's not just about the beat riding under the vocals; it's part of the aggression and atmosphere. It's not merely a song, it's a statement.

**After (EN):**
> The heavy beat adds to the aggressive tone.

**Keep the contrast** when the negative half corrects something the reader would otherwise assume:
> 이 API는 토큰을 갱신하지 않는다. 갱신은 별도의 refresh 엔드포인트가 맡는다.

### 2. One-line closers and dramatic fragments

**Before (KO):**
> 캐시를 붙이자 반복 요청 처리 시간이 절반으로 줄었다.
>
> 바로 이것이 핵심이다.

**After (KO):**
> 캐시를 붙이자 반복 요청 처리 시간이 절반으로 줄었다.

**Before (KO, fragment row):**
> 그리고 새 모델이 나왔다. 대칭에 대한 선호가 없다. 사람 눈에 익은 형태에 대한 미련도 없다. 기존 규칙은 사라졌다.

**After (KO):**
> 새 모델은 대칭이나 사람 눈에 익은 형태를 우대하지 않았고, 그래서 기존 규칙이 더는 통하지 않았다.

**Before (EN, repeated closer):**
> Caching cuts repeat work.
>
> That is the real win.
>
> Retries hide brief outages.
>
> That is the real win.

**After (EN):**
> Caching cuts repeat work. Retries hide brief outages.

### 3. Sayings that sound deep

**Before (KO):**
> 결국 중요한 것은 속도가 아니라 방향이다. 본질적으로 이 문제는 조직 문화의 문제다.

**After (KO):**
> 속도보다 방향이 문제다. 원인은 조직 문화에 있다.

**Before (EN):**
> At its core, the real question is what we value here.

**After (EN):**
> The team has to decide what it values here.

Note both Afters are shorter and say the same thing. The saying was the whole content, so removing it leaves the claim intact and nothing else.

### 4. Staged run-up before the point

**Before (KO):**
> 자, 그럼 본격적으로 하나씩 살펴보겠습니다. 들어가기에 앞서 짚어보면, 이번 장애의 원인은 커넥션 풀 설정이었습니다.

**After (KO):**
> 이번 장애의 원인은 커넥션 풀 설정이었다.

**Before (EN):**
> Let's dive in. Here's the thing: the API has a rate limit of 100 requests per minute.

**After (EN):**
> The API allows 100 requests per minute.

### 5. Arguing with no one

**Before (KO):**
> 물론 이 방식이 만능이라는 말은 아니다. 오해하지 말자, 기존 방식이 틀렸다는 뜻도 아니다. 다만 이 경우에는 새 방식이 더 빠르다.

**After (KO):**
> 이 경우에는 새 방식이 더 빠르다.

**Before (EN):**
> One might be tempted to reach for a database here, but a JSON file is enough for 200 records.

**After (EN):**
> A JSON file is enough for 200 records.

---

## B. Rhythm by rule

### 6. Forced triads

**Before (KO):**
> 이번 행사에서는 강연과 패널 토론, 네트워킹 기회를 제공합니다. 참가자들은 혁신과 영감, 그리고 업계 인사이트를 얻어 갈 수 있습니다.

**After (KO):**
> 이번 행사는 강연과 패널 토론으로 구성되고, 사이사이 참가자끼리 이야기 나눌 시간이 있다.

The second sentence in the Before adds no fact beyond the first, so it goes. The three real items in the first sentence collapse to two because "네트워킹 기회" is the informal time between sessions, not a third program track.

**Before (EN, paragraph scale):**
> A career can look promising and fail. A relationship can feel important and end. A skill can take years and remain useless. These decisions rarely explain themselves.

**After (EN):**
> A career can look promising and fail. So can a relationship that felt important and ended, or a skill that took years and remained useless. These decisions rarely explain themselves.

All three items survive here because each is a distinct case. Only the drumbeat shape changes.

### 7. Repeated sentence openings

**Before (KO):**
> 그는 문을 확인했다. 그는 문에 달린 자물쇠도 확인했다. 그는 둘 다 기억해 두었다.

**After (KO):**
> 그는 문과 거기 달린 자물쇠를 확인하고 둘 다 기억해 두었다.

**Before (EN):**
> She noted the door. She noted the lock on it. She filed both away.

**After (EN):**
> She noted the door and its lock, then filed both away.

Do not ban the repeated word. A remaining sentence may still start with `그는`, and writers repeat an opening on purpose for rhythm.

### 8. Dashes as universal connector

**Before (KO):**
> 새 정책은 (em dash) 사전 예고 없이 발표되었는데 (em dash) 수천 명에게 영향을 미친다.

**After (KO):**
> 사전 예고 없이 발표된 새 정책은 수천 명에게 영향을 미친다.

Korean replacements, in rough order of preference: restructure the sentence, comma, parentheses, 가운뎃점 for coordinate items (`서울·부산·대구`), a connective (`곧`, `즉`, `등`), or a full stop.

**Before (EN):**
> The new policy (em dash) announced without warning (em dash) affects thousands of workers. The changes -- long overdue according to critics -- take effect immediately.

**After (EN):**
> The new policy, announced without warning, affects thousands of workers. The changes, long overdue according to critics, take effect immediately.

Leave dashes and hyphens inside code blocks, inline code, commands, paths, and URLs alone. (This file writes the dash character as `(em dash)` on purpose, so that the file itself does not model the habit.)

### 9. Stacked qualifiers

**Before (KO):**
> 이 정책이 결과에 어느 정도 영향을 미칠 수도 있을 것으로 보이는 측면이 있다.

**After (KO):**
> 이 정책은 결과에 영향을 줄 수 있다.

**Before (EN):**
> It could potentially possibly be argued that the policy might have some effect on outcomes.

**After (EN):**
> The policy may affect outcomes.

One hedge survives in each After because the original claim really is uncertain. Removing it would strengthen a claim the writer did not make.

### 10. Hyphenated pairs everywhere (English only)

**Before:**
> The team is cross-functional, the report is high-quality, and the methodology is data-driven.

**After:**
> The team is cross functional, the report is high quality, and the methodology is data driven.

Keep the hyphen before a noun: `a high-quality report`.

### 11. Passive voice and hidden subjects

**Before (KO):**
> 이 문제는 여러 차례 지적되어졌고, 해결책도 제시되어진 바 있다. 결과는 자동으로 저장되어진다.

**After (KO):**
> 이 문제는 여러 차례 지적되었고, 해결책도 나왔다. 결과는 자동으로 저장된다.

**Before (EN):**
> No configuration file needed. The results are preserved automatically.

**After (EN):**
> You do not need a configuration file. The system preserves the results automatically.

Korean 이중피동 is a grammatical error, not a stylistic preference, so it never counts as *weak alone*.

---

## C. Inflation and borrowed authority

The fact underneath is usually sound. Keep it and remove the dressing. Where the dressing is the only content, the sentence goes.

### 12. Overused AI vocabulary

**Before (KO):**
> 이 도구는 CSV 변환과 일괄 이름 변경 등 다양한 기능을 제공하는 혁신적인 솔루션으로, 생산성 극대화에 필수적인 역할을 합니다.

**After (KO):**
> 이 도구는 CSV 변환과 일괄 이름 변경을 지원한다.

**Before (EN):**
> This robust solution delves into the evolving landscape of CSV processing, showcasing a meticulous streaming approach that handles files larger than memory.

**After (EN):**
> This tool processes CSV files in streaming mode, so it handles files larger than memory.

Keep technical senses of the watched words: `robust regression`, `gated recurrent unit`, `키 값`, `랜드스케이프 모드`.

### 13. Inflated significance

**Before (KO):**
> 이번 발표는 업계의 새 지평을 연 사건으로, 시사하는 바가 크다. 이후 두 분기 동안 경쟁사 세 곳이 비슷한 기능을 내놓으며 이 회사는 업계 선두로 자리매김했다.

**After (KO):**
> 발표 후 두 분기 동안 경쟁사 세 곳이 비슷한 기능을 내놓았다.

**Before (EN):**
> Her 1978 paper stands as a testament to enduring craft, marking a pivotal moment in the evolving landscape of the field.

**After (EN):**
> She published the method in 1978.

Each After keeps only what the Before actually established. The significance claims had no evidence behind them, so there is nothing to carry over. Boilerplate section headings that exist only to inflate go the same way: `도전 과제와 전망`, `향후 계획`, `Challenges and Legacy`, `Future Outlook`.

### 14. Vague connection

**Before (KO):**
> 이 지표는 사용자 이탈률과 관련되어 있으며, 매출과도 맞닿아 있다.

**After (KO):**
> 이 지표는 사용자 이탈률과 함께 움직인다. 매출과의 관계는 확인되지 않았다.

If even the direction of the relationship is unknown, cut the sentence and ask the writer what they meant. Do not upgrade `관련되어 있다` into a causal claim.

**Before (EN):**
> The compound is associated with improved outcomes.

**After (EN):**
> Patients taking the compound recovered sooner.

That After is only correct if the Before's source says so. When the text gives you nothing but the association, keep the association and leave the mechanism alone.

### 15. Shallow riders

A trailing clause that restates the main clause instead of adding to it.

**Before (KO):**
> 팀은 배포 주기를 이틀로 줄여, 개발 생산성 향상에 기여하며 조직의 민첩성을 강화하고 있다.

**After (KO):**
> 팀은 배포 주기를 이틀로 줄였다.

**Before (EN):**
> The company opened three branches, two of them outside its home region, underscoring its commitment to growth and highlighting its expanding reach.

**After (EN):**
> The company opened three branches, two of them outside its home region.

### 16. Sales language

**Before (KO):**
> 시청역에서 도보 5분 거리, 도심 한복판에 자리한 이 호텔은 숨 막히는 전망을 선사하며 놓칠 수 없는 다채로운 경험을 자랑합니다.

**After (KO):**
> 이 호텔은 시청역에서 걸어서 5분 거리다.

**Before (EN):**
> Nestled in the heart of the countryside 12 km from the nearest town, this breathtaking must-visit destination boasts a diverse array of activities.

**After (EN):**
> The site is 12 km from the nearest town.

The sales words disappear and the one checkable fact stays. If the writer wants the activities listed, they have to say which ones.

### 17. Borrowed authority

**Before (KO):**
> 전문가들은 이 방식이 더 효율적이라고 말한다. 업계에서도 비슷한 평가가 나온다.

**After (KO):**
> 이 방식이 더 효율적이라는 평가가 있다. (누가 언제 그렇게 평가했는지 원문에 없다면, 출처를 확인해 채우거나 문장을 뺀다.)

**Before (EN):**
> Experts argue this is the superior approach, and industry reports confirm its growing adoption.

**After (EN):**
> Some people prefer this approach. (Name the source, or cut the sentence.)

Never manufacture an attribution to fill the gap. An unsourced claim stated plainly is honest; an invented citation is not.

### 18. Avoiding plain verbs

**Before (KO):**
> 이 모듈은 인증 처리의 역할을 하며, 세션 관리 기능을 담당한다. 설정 파일은 기본값을 의미한다.

**After (KO):**
> 이 모듈은 인증과 세션 관리를 처리한다. 설정 파일에는 기본값이 들어 있다.

**Before (EN):**
> The module serves as the entry point and functions as a router. The config file represents the defaults.

**After (EN):**
> The module is the entry point and routes requests. The config file holds the defaults.

---

## D. Formatting by rule

### 19. Bold as decoration

**Before:**
> - **속도**: 요청 처리 시간이 절반으로 줄었다.
> - **안정성**: 재시도 로직으로 일시적 오류를 흡수한다.
> - **비용**: 인스턴스 수를 두 대 줄였다.
>
> 이 세 가지는 **모두** 같은 변경에서 나왔다.

**After:**
> 요청 처리 시간이 절반으로 줄었고, 재시도 로직이 일시적 오류를 흡수한다. 인스턴스도 두 대 줄였다. 모두 같은 변경에서 나온 결과다.

Bold survives only as a genuine label a reader scans for, such as a term being defined. Never bold a word for emphasis inside a sentence. When you remove the bold labels from a list, check whether the list should have been prose all along.

### 20. Decorative headings

Match the document's existing convention. If other headings are sentence case, make these sentence case. Drop headings from a text too short to need them, and never add a heading the original did not have.

### 21. Curly quotation marks (English only)

Convert curly quotes to straight `"` and `'` unless the original is consistently curly throughout. Leave quotes inside code untouched.

---

## E. Leftovers

### 23. Knowledge-limit disclaimers and guesses

**Before (KO):**
> 공개된 정보에 따르면 이 회사는 2015년에 설립되었으며, 구체적인 창업자 정보는 알려지지 않았다.

**After (KO):**
> 이 회사는 2015년에 설립되었다.

The disclaimer is the model talking about its own retrieval, not a fact about the company. Drop it. Keep a genuine "unknown" only when the writer means it as information: `창업자는 공개된 적이 없다` is a claim about the company and stays.

### 24. Heading repeated in the first sentence

**Before:**
> ## 캐시 설정
> 캐시 설정은 캐시 동작을 정하는 설정이다. 만료 시간, 최대 크기, 축출 정책을 지정할 수 있다.

**After:**
> ## 캐시 설정
> 만료 시간, 최대 크기, 축출 정책을 지정할 수 있다.

### 22 and 25

Pure deletions with nothing to demonstrate. Phrase lists are in `ai-tells.md`.

---

## Korean corrections

Not AI tells but plain editing errors. SKILL.md names them; these are the fixes.

### 번역투

| Before | After | Note |
|---|---|---|
| 회사의 성장의 원인 | 회사가 성장한 원인 | stacked 소유격 `의` |
| 많은 사용자들이 문제들을 겪었다 | 많은 사용자가 문제를 겪었다 | `들` where Korean does not pluralize |
| 이 기능은 중요성을 가진다 | 이 기능은 중요하다 | `가지다` for *have* |
| 성능에 대해서 개선이 있었다 | 성능이 개선되었다 | `~에 대해서` padding |
| 설계에 있어서 핵심은 | 설계의 핵심은 | `~에 있어서` |
| 효율적으로 처리를 하는 것이다 | 효율적으로 처리한다 | `~하는 것이다` padding |
| 이 연구는 ~을 보여준다 | 이 연구에서 ~이 드러났다 | inanimate subject acting |
| JSON, XML과 같은 형식 | JSON이나 XML 같은 형식 | *such as* 직역 |
| 지속적으로 개선되어 오고 있다 | 계속 개선하고 있다 | present-perfect 직역 |
| 사용자로 하여금 ~하게 만든다 | 사용자가 ~할 수 있다 | *make + O + V* 직역 |
| 기술적인 이슈들에 대한 대응적 접근 | 기술 문제에 대응하는 방식 | `~적(的)` piled on |

### Mechanics

- 조사 agreement: 은/는, 이/가, 을/를, 와/과, (으)로 after the right final consonant.
- 띄어쓰기: 의존명사 (수, 것, 때, 뿐, 지) spaced; 보조용언 spacing consistent within a document.
- 사이시옷: 나뭇잎, 촛불, 횟수, and not where it does not belong (개수, 초점, 대가).
- 두음법칙: 여성, 연도, 이자율 in initial position.
- 종결어미 consistency: never mix 해요체, 합쇼체, and 평어체 in one passage.
