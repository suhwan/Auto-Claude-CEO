# Summary: 10-03 수동 검증 UI (UAT)

## Overview
GSD 탭에 수동 검증(UAT) UI를 추가했습니다. Plan 실행 후 Auto-Claude QA를 통과한 결과물을 사용자가 직접 검증하고 Approve/Reject 할 수 있는 인터페이스를 제공합니다.

## Changes Made

### Backend Service (`apps/frontend/src/main/gsd-service.ts`)
- `VerificationStatus`, `GsdVerificationItem`, `GsdPlanVerification`, `GsdVerificationHistory` 타입 추가
- `getPendingVerifications()` - STATE.md에서 완료된 플랜을 파싱하여 검증 대기 목록 반환
- `submitVerification()` - 승인/거부 결과를 verifications.json에 저장
- `createFixRequest()` - 거부 시 fix_requests 디렉토리에 FIX-REQUEST.md 파일 생성
- `getDefaultChecklist()` - PLAN.md의 success_criteria에서 체크리스트 추출

### IPC Layer
- `apps/frontend/src/shared/constants/ipc.ts`: GSD_GET_PENDING_VERIFICATIONS, GSD_SUBMIT_VERIFICATION 채널 추가
- `apps/frontend/src/main/ipc-handlers/gsd-handlers.ts`: 검증 관련 IPC 핸들러 구현
- `apps/frontend/src/preload/api/modules/gsd-api.ts`: 검증 타입 및 API 메서드 추가

### UI Components
- `apps/frontend/src/renderer/components/gsd/VerificationPanel.tsx` (신규)
  - VerificationPanel: 체크리스트, 피드백 입력, Approve/Reject 버튼
  - VerificationBadge: 상태별 배지 (pending, approved, rejected, not_required)
- `apps/frontend/src/renderer/components/gsd/index.ts`: 컴포넌트 export 추가
- `apps/frontend/src/renderer/components/GsdView.tsx`: 검증 UI 통합
  - pendingVerifications 상태 관리
  - handleApprove, handleReject 핸들러
  - Phase list 상단에 검증 패널 섹션 추가

### i18n
- `apps/frontend/src/shared/i18n/locales/en/navigation.json`: 17개 검증 관련 키 추가
- `apps/frontend/src/shared/i18n/locales/fr/navigation.json`: 17개 검증 관련 키 추가 (프랑스어)

### Browser Mock
- `apps/frontend/src/renderer/lib/browser-mock.ts`: getPendingVerifications, submitVerification mock 추가

## Verification Features

### UI Flow
1. Plan 완료 후 STATE.md에 기록된 완료된 플랜 표시
2. VerificationPanel에서:
   - Auto-Claude QA 통과 상태 표시
   - success_criteria 기반 체크리스트 표시
   - 피드백 입력 (거부 시 필수)
   - Approve/Reject 버튼

### Data Flow
- Approve 클릭: verifications.json에 approved 상태 저장
- Reject 클릭:
  - verifications.json에 rejected 상태 저장
  - `.planning/fix_requests/{planId}-FIX-REQUEST.md` 파일 생성
  - `/gsd:plan-fix` 명령으로 수정 플랜 생성 가능

## Commits
1. `feat(10-03): GsdService에 검증 상태 관리 추가`
2. `feat(10-03): IPC 핸들러 및 Preload API 추가`
3. `feat(10-03): VerificationPanel 컴포넌트 구현`
4. `feat(10-03): GsdView에 검증 UI 통합`
5. `feat(10-03): gsd 컴포넌트 export 및 i18n 업데이트`
6. `chore(10-03): browser-mock에 검증 API mock 추가`

## Files Changed
- `apps/frontend/src/main/gsd-service.ts` (수정)
- `apps/frontend/src/main/ipc-handlers/gsd-handlers.ts` (수정)
- `apps/frontend/src/preload/api/modules/gsd-api.ts` (수정)
- `apps/frontend/src/shared/constants/ipc.ts` (수정)
- `apps/frontend/src/renderer/components/gsd/VerificationPanel.tsx` (신규)
- `apps/frontend/src/renderer/components/gsd/index.ts` (수정)
- `apps/frontend/src/renderer/components/GsdView.tsx` (수정)
- `apps/frontend/src/shared/i18n/locales/en/navigation.json` (수정)
- `apps/frontend/src/shared/i18n/locales/fr/navigation.json` (수정)
- `apps/frontend/src/renderer/lib/browser-mock.ts` (수정)
