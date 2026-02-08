import { router } from "../trpc";
import { workspaceRouter } from "./workspace";
import { channelRouter } from "./channel";
import { messageRouter } from "./message";
import { threadRouter } from "./thread";
import { diveRouter } from "./dive";
import { agentRouter } from "./agent";
import { searchRouter } from "./search";

export const appRouter = router({
  workspace: workspaceRouter,
  channel: channelRouter,
  message: messageRouter,
  thread: threadRouter,
  dive: diveRouter,
  agent: agentRouter,
  search: searchRouter,
});

export type AppRouter = typeof appRouter;
