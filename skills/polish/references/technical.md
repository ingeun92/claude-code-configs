# Technical mode: STE-style editing

An optional mode of the polish skill. It borrows the writing rules of ASD-STE100 (Simplified Technical English) so that procedures and reference text are short, literal, and hard to misread. The goal changes from "sounds like this person" to "nobody can misread it".

Call the result STE-style, never STE-compliant. Real compliance needs the STE approved-word dictionary and a checker, and neither is part of this skill. If the user asks for certified compliance, say so.

## When it applies

- The user asks for it: `STE로`, `STE 스타일로`, `기술문서처럼`, `매뉴얼처럼`, `STE`, `technical style`.
- Embedded mode, when the caller hands over a procedure, runbook step, or error message.

Otherwise stay in the default mode. A README's prose sections are not procedures just because the file has steps elsewhere; apply this mode only to the steps.

## What changes

- **Suspended:** "Vary sentence length" in the Draft step, and voice preservation for word choice and rhythm. Uniform sentences are the point here.
- **Still binding:** non-negotiables 1 to 3 (input language, every claim, no fabrication), the Korean corrections, the AI tells, and the output rules.
- **Never touched:** code, commands, paths, UI labels, quoted error strings, product names. Match a UI label character for character, even when the label is clumsy.

## Rules for Korean and English

1. **Sort first.** Each sentence either tells the reader to do something (procedure) or explains something (description). Do not mix the two in one sentence.
2. **One instruction per sentence.** Two actions share a sentence only when the reader does them at the same time.
3. **Sequences become numbered lists.** One action per step. Keep the order the original gives.
4. **Condition first.** `X이면 Y를 하세요`, `If X, do Y`. Put the condition or location before the command.
5. **Short sentences.** English: at most 20 words in a procedure, 25 in a description. Korean has no official count; use one predicate per step (plus a condition clause), and at most two clauses in a description.
6. **Short paragraphs.** One topic each, six sentences at most.
7. **One term, one meaning.** Pick one name for each thing and keep it (do not rotate 설정, 구성, 환경설정 for elegance). Keep the writer's term when it matches the code or UI.
8. **Active voice in procedures.** Name the actor. In descriptions, passive is acceptable when the actor is unknown or irrelevant.
9. **Warnings come before the step they guard.** Start with the instruction, then the consequence: `Do not X. Y can occur.`
10. **Break noun stacks.** English: at most three nouns in a row. Korean: split chains like `설정 파일 경로 검증 오류 처리` with 조사 (`설정 파일 경로를 검증할 때 생기는 오류의 처리`).
11. **Replace vague conditions only from the text.** `필요 시`, `적절히`, `as needed`, `appropriately`: if the text states the real condition elsewhere, use it. If not, keep the vague word and mention it in the closing note. Never invent the condition.
12. **Imperative register stays consistent.** Use the original's form (`~하세요`, `~하십시오`, `~한다`) for every step.

## English only

- **No -ing forms** outside technical names: `Before installing` → `Before you install`; `by restarting the service` → `restart the service`.
- **Simple tenses:** present, past, future. Avoid perfect and progressive forms in procedures.
- **No telegraphic style.** Keep articles and `that`.
- **Plain words, one sense each:** ensure → make sure; utilize, leverage → use; prior to → before; in order to → to; perform → do; terminate → stop; commence → start; subsequently → then; approximately → about; allows you to → lets you.

## Examples

**Before (KO):**
> 설치를 진행하기 전에 기존 설정 파일이 백업되어 있는지 확인하는 것이 필요하며, 필요 시 `--force` 옵션을 사용하여 덮어쓰기를 진행할 수 있습니다.

**After (KO):**
> 1. 설치하기 전에 기존 설정 파일을 백업했는지 확인하십시오.
> 2. 기존 파일을 덮어쓰려면 `--force` 옵션을 붙이십시오.

**Before (EN):**
> Prior to running the migration, it is important to ensure that the database has been backed up, as failing to do so could potentially result in data loss.

**After (EN):**
> Make sure that the database is backed up before you run the migration. If it is not, data loss can occur.
