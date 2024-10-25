import type { MessageType } from "@/lib/enums.ts";

export default interface IMessage {
    type: MessageType;
    title?: string;
    data?: any;
    finish?: boolean;
    error?: boolean;
    tokens?: number;
}