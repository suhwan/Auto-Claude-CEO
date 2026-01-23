# Summary: 12-01 Ideas to GSD Chat UI

## Outcome
Implemented a conversational chat-based interface for converting Ideation ideas into GSD projects. Users can now click a "GSD Project" button on any idea card to open a dialog that starts a conversation with Claude to define project requirements and create a full GSD project structure.

## Tasks Completed
- [x] Task 1: Extend types - Added `gsd_converted` status and `gsdProjectPath` field to insight types
- [x] Task 2: Add GSD button - Added FolderGit2 icon button to IdeaCard with i18n support (EN/FR)
- [x] Task 3: Create GsdChatDialog - Built full chat UI component with streaming messages, user input, and completion states
- [x] Task 4: Implement IPC handlers - Added ChatGenerator class and IPC handlers for chat session management
- [x] Task 5: Extend GSD API - Added preload bridge methods for startChatSession, sendChatMessage, endChatSession
- [x] Task 6: Integrate in Ideation - Wired up all components with state management and event handling

## Commits
- `a219b84e` - feat(12-01): extend IdeationStatus and IdeaBase types for GSD conversion
- `6852f879` - feat(12-01): add GSD Project conversion button to IdeaCard
- `47b4906b` - feat(12-01): create GsdChatDialog component for chat-based conversion
- `d5dd185a` - feat(12-01): implement GSD Chat IPC handlers for conversational sessions
- `f7dcb38b` - feat(12-01): extend GSD API with chat session methods for preload bridge
- `7c7d02d4` - feat(12-01): integrate GSD conversion in Ideation view

## Files Changed
- `apps/frontend/src/shared/types/insights.ts` - Added 'gsd_converted' status and gsdProjectPath field
- `apps/frontend/src/renderer/components/ideation/IdeaCard.tsx` - Added GSD conversion button with FolderGit2 icon
- `apps/frontend/src/shared/i18n/locales/en/common.json` - Added convertToGsdAriaLabel, goToGsdProjectAriaLabel
- `apps/frontend/src/shared/i18n/locales/fr/common.json` - Added French translations for GSD aria labels
- `apps/frontend/src/shared/i18n/locales/en/navigation.json` - Added chatDialog i18n keys
- `apps/frontend/src/shared/i18n/locales/fr/navigation.json` - Added French chatDialog translations
- `apps/frontend/src/renderer/components/gsd/GsdChatDialog.tsx` - New chat dialog component (270+ lines)
- `apps/frontend/src/shared/constants/ipc.ts` - Added GSD_START_CHAT_SESSION, GSD_SEND_CHAT_MESSAGE, GSD_END_CHAT_SESSION
- `apps/frontend/src/main/gsd-service.ts` - Added ChatGenerator class for bidirectional Claude CLI communication
- `apps/frontend/src/main/ipc-handlers/gsd-handlers.ts` - Added IPC handlers for chat session management
- `apps/frontend/src/preload/api/modules/gsd-api.ts` - Added GsdChatInput interface and chat API methods
- `apps/frontend/src/renderer/stores/ideation-store.ts` - Added setIdeaGsdPath method
- `apps/frontend/src/renderer/components/ideation/Ideation.tsx` - Integrated GsdChatDialog with handlers
- `apps/frontend/src/renderer/App.tsx` - Updated Ideation component call with projectPath prop

## Deviations
None

## Notes
- The ChatGenerator spawns Claude CLI with `/gsd:new-project` command and handles bidirectional stdin/stdout communication
- Chat events are forwarded via IPC from main process to renderer: `gsd:chat:message`, `gsd:chat:error`, `gsd:chat:complete`
- The dialog auto-scrolls to bottom as new messages arrive and shows a typing indicator during streaming
- Completion is detected when Claude creates `.planning/PROJECT.md` file
- Ideas converted to GSD projects are marked with `gsd_converted` status and store the path in `gsdProjectPath`
