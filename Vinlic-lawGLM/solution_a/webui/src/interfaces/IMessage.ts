import type { MessageType } from "@/enums";

export default interface IMessage {
    id?: string;
    type: MessageType;
    title?: string;
    data?: any;
    error?: boolean;
    finish?: boolean;
    tokens?: number;
}