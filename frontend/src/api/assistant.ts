import client from "./client";

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export const chat = (messages: ChatMessage[]) =>
  client.post<{ reply: string }>("/assistant/chat", { messages });
